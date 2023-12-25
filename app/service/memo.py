import json

import aioredis
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from fastapi import Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.security import get_current_user, check_length, time_now
from app.db.database import get_db, save_db, get_redis_client
from app.db.models import Memo, User
from app.core.aiRequset import GPTService
from app.schemas.request import CreateMemoRequest, UpdateMemoRequest
from app.service.abstract import AbstractDiaryService

class MemoService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db), redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def create(self, memo_data: CreateMemoRequest) -> Memo:

        # url이면 title을 가져옴
        gpt_service = GPTService(self.user, self.db)
        if memo_data.content.startswith('http://') or memo_data.content.startswith('https://'):
            async with ClientSession() as session:
                async with session.get(memo_data.content) as response:
                    html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                title = soup.title.string if soup.title else "No title"
            if title == "No title":
                content = f"title = URL 주소, content = {memo_data.content}"
            else:
                content = f"title = {title}, content = {memo_data.content}"
            data = await gpt_service.send_gpt_request(8, content)

        else:
            data = await gpt_service.send_gpt_request(8, memo_data.content)

        # 제목이 없다면 자동 생성
        data = json.loads(data)
        if memo_data.title == "":
            memo_data.title = data['title']

        # 제목, 내용 길이 체크
        await check_length(text=memo_data.title, max_length=255, error_code=4023)
        await check_length(text=memo_data.content, max_length=1000, error_code=4221)

        # 메모 생성
        now = await time_now()
        memo = Memo(
            title=memo_data.title,
            content=memo_data.content,
            User_id=self.user.id,
            tags=json.dumps(data['tags'], ensure_ascii=False),
            create_date=now,
            modify_date=now,
        )
        memo = save_db(memo, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"memo:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # 메모 반환
        return memo

    async def read(self, memo_id: int) -> Memo:
        memo = self.db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == self.user.id, Memo.is_deleted == False).first()

        # 메모가 없을 경우 예외 처리
        if not memo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4016,
            )

        # 메모 반환
        return memo

    async def update(self, memo_id: int, memo_data: UpdateMemoRequest) -> Memo:
        # 메모 조회
        memo = self.db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == self.user.id, Memo.is_deleted == False).first()

        # 메모가 없을 경우 예외 처리
        if not memo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4016,
            )

        # 메모 수정
        if memo_data.title != "":
            await check_length(text=memo_data.title, max_length=255, error_code=4023)
            memo.title = memo_data.title
        if memo_data.content != "":
            await check_length(text=memo_data.content, max_length=1000, error_code=4221)
            memo.content = memo_data.content
        memo.modify_date = await time_now()
        memo = save_db(memo, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"memo:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # 메모 반환
        return memo

    async def delete(self, memo_id: int) -> None:
        # 메모 조회
        memo = self.db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == self.user.id, Memo.is_deleted == False).first()

        # 메모가 없을 경우 예외 처리
        if not memo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4016,
            )

        # 메모 삭제
        memo.is_deleted = True
        save_db(memo, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"memo:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

    async def list(self, page: int, background_tasks: BackgroundTasks) -> dict:
        async def cache_next_page(page: int, total_count: int) -> None:
            limit, offset = (7, 0) if page == 1 else (8, 7 + (page - 2) * 8)
            memos = self.db.query(Memo).filter(Memo.User_id == self.user.id,
                                                        Memo.is_deleted == False).order_by(
                Memo.create_date.desc()).limit(limit).offset(offset).all()
            memos_dict_list = []
            for memo in memos:
                memo_dict = memo.__dict__.copy()
                memo_dict.pop('_sa_instance_state', None)
                memo_dict["diary_type"] = 3
                memos_dict_list.append(memo_dict)
            redis_key = f"memo:list:{self.user.id}:{page}"
            await self.redis.set(redis_key, json.dumps({"list": memos_dict_list, "count": limit, "total_count": total_count}, default=str, ensure_ascii=False), ex=1800)


        # 캐싱된 데이터가 있을 경우 캐싱된 데이터 반환 + 다음 페이지 캐싱
        redis_key = f"memo:list:{self.user.id}:{page}"
        cached_data = await self.redis.get(redis_key)
        if cached_data:
            json_data = json.loads(cached_data)
            background_tasks.add_task(cache_next_page, page + 1, json_data["total_count"])
            return json_data

        # 캐싱된 데이터가 없을 경우 데이터베이스에서 조회
        limit, offset = (7, 0) if page == 1 else (8, 7 + (page - 2) * 8)
        memos = self.db.query(Memo).filter(Memo.User_id == self.user.id, Memo.is_deleted == False).order_by(Memo.create_date.desc()).limit(limit).offset(offset).all()
        total_count = self.db.query(Memo).filter(Memo.User_id == self.user.id, Memo.is_deleted == False).count()

        # 각 메모 객체를 사전 형태로 변환하고 새로운 키-값 쌍 추가
        memos_dict_list = []
        for memo in memos:
            memo_dict = memo.__dict__.copy()
            memo_dict.pop('_sa_instance_state', None)
            memo_dict["diary_type"] = 3
            memos_dict_list.append(memo_dict)

            # 다음 페이지 캐싱
        background_tasks.add_task(cache_next_page, page + 1, total_count)
        await self.redis.set(redis_key, json.dumps({"list": memos_dict_list, "count": limit, "total_count": total_count}, default=str, ensure_ascii=False), ex=1800)

        # 메모 리스트 반환
        return {"list": memos_dict_list, "count": limit, "total_count": total_count}
