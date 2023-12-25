import asyncio
import json
import aioredis
from fastapi import Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.security import get_current_user, check_length, time_now, datetime_serializer, diary_serializer
from app.db.database import get_db, save_db, get_redis_client
from app.db.models import User, NightDiary
from app.core.aiRequset import GPTService
from app.schemas.request import CreateDiaryRequest
from app.service.abstract import AbstractDiaryService


class DiaryService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db), redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def create(self, diary_data: CreateDiaryRequest) -> NightDiary:

        gpt_service = GPTService(self.user, self.db)
        if diary_data.title == "":
            # 이미지와 다이어리 제목 생성
            content = diary_data.content
            image_info, diary_name = await asyncio.gather(
                gpt_service.send_dalle_request(content),
                gpt_service.send_gpt_request(2, content)
            )
        else:
            diary_name = diary_data.title
            content = diary_data.content
            image_info = await gpt_service.send_dalle_request(content)

        # 이미지 background color 문자열로 변환
        image_url, upper_dominant_color, lower_dominant_color = image_info
        upper_lower_color = "[\"" + str(upper_dominant_color) + "\", \"" + str(lower_dominant_color) + "\"]"

        # 저녁 일기 db에 저장
        await check_length(diary_name, 255, 4023)
        await check_length(content, 1000, 4221)
        now = await time_now()
        if diary_data.date == "":
            diary_data.date = now
        diary = NightDiary(
            content=content,
            User_id=self.user.id,
            image_url=image_url,
            background_color=upper_lower_color,
            diary_name=diary_name,
            create_date=diary_data.date,
            modify_date=now,
        )
        diary = save_db(diary, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"diary:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # 새로운 cache 생성
        redis_key = f"diary:{self.user.id}:{diary.id}"
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        # 다이어리 반환
        return diary

    async def read(self, diary_id: int, background_tasks: BackgroundTasks) -> NightDiary:

        async def count_view(diary_id: int) -> None:
            diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).first()
            diary.view_count += 1
            save_db(diary, self.db)

        # 캐싱된 데이터가 있는지 확인
        redis_key = f"diary:{self.user.id}:{diary_id}"
        redis_data = await self.redis.get(redis_key)
        if redis_data:
            background_tasks.add_task(count_view, diary_id)
            return json.loads(redis_data)

        # 다이어리 조회
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4012,
            )

        # 데이터 캐싱
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        # 다이어리 반환
        return diary

    async def update(self, diary_id: int, diary_data: CreateDiaryRequest) -> NightDiary:
        # 다이어리 조회
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4012,
            )

        if diary_data.title != "":
            await check_length(diary_data.title, 255, 4023)
            diary.diary_name = diary_data.title
        if diary_data.content != "":
            await check_length(diary_data.content, 1000, 4221)
            diary.content = diary_data.content
        diary.modify_date = await time_now()
        diary = save_db(diary, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"diary:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # diary cache 삭제
        redis_key = f"diary:{self.user.id}:{diary_id}"
        await self.redis.delete(redis_key)

        # 다이어리 반환
        return diary

    async def delete(self, diary_id: int) -> None:
        redis = await get_redis_client()
        # 다이어리 조회
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4012,
            )
        # 다이어리 삭제
        diary.is_deleted = True
        diary = save_db(diary, self.db)

        # history cache 삭제
        now = await time_now()
        redis_key = f"history:{self.user.id}:{now.day}"
        cached_data = await redis.get(redis_key)
        if cached_data:
            datas = json.loads(cached_data)
            is_exist = False
            for data in datas["NightDiary"]:
                if data == diary.id:
                    is_exist = True
            for data in datas["NightDiary"]:
                if data == diary.id:
                    is_exist = True
            if is_exist:
                await redis.delete(redis_key)

        # list cache 삭제
        keys = await self.redis.keys(f"diary:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # diary cache 삭제
        await redis.delete(f"diary:{self.user.id}:{diary.id}")

    async def list(self, page: int, background_tasks: BackgroundTasks) -> dict:

        async def cache_next_page(page: int, total_count: int) -> None:
            limit, offset = (7, 0) if page == 1 else (8, 7 + (page - 2) * 8)
            diaries = self.db.query(NightDiary).filter(NightDiary.User_id == self.user.id,
                                                        NightDiary.is_deleted == False).order_by(
                NightDiary.create_date.desc()).limit(limit).offset(offset).all()
            diaries_dict_list = []
            for diary in diaries:
                diary_dict = diary.__dict__.copy()
                diary_dict.pop('_sa_instance_state', None)
                diary_dict["diary_type"] = 2
                diaries_dict_list.append(diary_dict)
            redis_key = f"diary:list:{self.user.id}:{page}"
            await self.redis.set(redis_key,
                            json.dumps({"list": diaries_dict_list, "count": limit, "total_count": total_count},
                                       default=str, ensure_ascii=False), ex=1800)

        # 캐싱된 데이터가 있는지 확인
        redis_key = f"diary:list:{self.user.id}:{page}"
        cached_data = await self.redis.get(redis_key)

        # 캐싱된 데이터가 있을 경우 캐싱된 데이터 반환 + 다음 페이지 캐싱
        if cached_data:
            json_data = json.loads(cached_data)
            background_tasks.add_task(cache_next_page, page + 1, json_data["total_count"])
            return json_data

        # 캐싱된 데이터가 없을 경우 데이터베이스에서 조회
        limit, offset = (7, 0) if page == 1 else (8, 7 + (page - 2) * 8)
        diaries = self.db.query(NightDiary).filter(NightDiary.User_id == self.user.id,
                                                    NightDiary.is_deleted == False).order_by(
            NightDiary.create_date.desc()).limit(limit).offset(offset).all()

        total_count = self.db.query(NightDiary).filter(NightDiary.User_id == self.user.id,
                                                         NightDiary.is_deleted == False).count()

        # 각 꿈 객체를 사전 형태로 변환하고 새로운 키-값 쌍 추가
        diaries_dict_list = []
        for diary in diaries:
            diary_dict = diary.__dict__.copy()
            diary_dict.pop('_sa_instance_state', None)
            diary_dict["diary_type"] = 2
            diaries_dict_list.append(diary_dict)

        # 다음 페이지 캐싱
        background_tasks.add_task(cache_next_page, page + 1, total_count)
        await self.redis.set(redis_key, json.dumps({"list": diaries_dict_list, "count": limit, "total_count": total_count},
                                              default=str, ensure_ascii=False), ex=1800)

        # 다이어리 반환
        return {"list": diaries_dict_list, "count": limit, "total_count": total_count}