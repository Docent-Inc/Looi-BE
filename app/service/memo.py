import json
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import get_current_user, check_length, time_now
from app.db.database import get_db, save_db
from app.db.models import Memo, User
from app.feature.aiRequset import GPTService
from app.schemas.request import CreateMemoRequest, UpdateMemoRequest
from app.service.abstract import AbstractDiaryService

class MemoService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        self.user = user
        self.db = db

    async def create(self, body: CreateMemoRequest) -> Memo:
        async def fetch_content_from_url(session: ClientSession, url: str) -> str:
            # url로부터 html content를 가져옴
            async with session.get(url) as response:
                return await response.text()

        content = body.content

        # url이면 title을 가져옴
        if content.startswith('http://') or content.startswith('https://'):
            async with ClientSession() as session:
                html_content = await fetch_content_from_url(session, content)
                soup = BeautifulSoup(html_content, 'html.parser')
                title = soup.title.string if soup.title else "No title"
                if title == "No title":
                    content = f"title = URL 주소, content = {content}"
                else:
                    content = f"title = {title}, content = {content}"

        # gpt-3.5 요청
        gpt_service = GPTService(self.user, self.db)
        data = await gpt_service.send_gpt_request(8, content)
        data = json.loads(data)

        # 제목이 없다면 자동 생성
        if body.title == "":
            body.title = data['title']

        # 제목, 내용 길이 체크
        await check_length(text=body.title, max_length=255, error_code=4023)
        await check_length(text=body.content, max_length=1000, error_code=4221)

        # 메모 생성
        now = await time_now()
        memo = Memo(
            title=body.title,
            content=content,
            User_id=self.user.id,
            tags=json.dumps(data['tags'], ensure_ascii=False),
            create_date=now,
            modify_date=now,
        )
        memo = save_db(memo, self.db)

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

    async def update(self, memo_id: int, body: UpdateMemoRequest) -> Memo:
        # 메모 조회
        memo = self.db.query(Memo).filter(Memo.id == memo_id, Memo.User_id == self.user.id, Memo.is_deleted == False).first()

        # 메모가 없을 경우 예외 처리
        if not memo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4016,
            )

        # 메모 수정
        if body.title != "":
            await check_length(text=body.title, max_length=255, error_code=4023)
            memo.title = body.title
        if body.content != "":
            await check_length(text=body.content, max_length=1000, error_code=4221)
            memo.content = body.content
        memo.modify_date = await time_now()
        memo = save_db(memo, self.db)

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

    async def list(self, page: int) -> list:
        # 메모 리스트 조회
        memos = self.db.query(Memo).filter(Memo.User_id == self.user.id, Memo.is_deleted == False).order_by(Memo.create_date.desc()).limit(10).offset((page - 1) * 10).all()
        total_count = self.db.query(Memo).filter(Memo.User_id == self.user.id, Memo.is_deleted == False).count()

        # 각 메모 객체를 사전 형태로 변환하고 새로운 키-값 쌍 추가
        memos_dict_list = []
        for memo in memos:
            memo_dict = memo.__dict__.copy()
            memo_dict.pop('_sa_instance_state', None)
            memo_dict["diary_type"] = 3
            memos_dict_list.append(memo_dict)

        # 총 개수와 페이지당 개수 정보 추가
        memos_dict_list.append({"count": 10, "total_count": total_count})

        # 변환된 메모 리스트 반환
        return memos_dict_list
