import asyncio

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, check_length, time_now
from app.db.database import get_db, save_db
from app.db.models import User, NightDiary, MorningDiary, Memo
from app.feature.aiRequset import GPTService
from app.feature.generate import image_background_color
from app.schemas.request import CreateDiaryRequest
from app.service.abstract import AbstractDiaryService


class DiaryService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        self.user = user
        self.db = db

    async def create(self, diary_data: CreateDiaryRequest) -> NightDiary:

        gpt_service = GPTService(self.user, self.db)
        if diary_data.title == "":
            # 이미지와 다이어리 제목 생성
            content = diary_data.content
            image_url, diary_name = await asyncio.gather(
                gpt_service.send_dalle_request(content),
                gpt_service.send_gpt_request(2, content)
            )
        else:
            diary_name = diary_data.title
            content = diary_data.content
            image_url = await gpt_service.send_dalle_request(content)

        # 이미지 배경색 추출
        upper_dominant_color, lower_dominant_color = await image_background_color(image_url)

        # 이미지 background color 문자열로 변환
        upper_lower_color = "[\"" + str(upper_dominant_color) + "\", \"" + str(lower_dominant_color) + "\"]"

        # 저녁 일기 db에 저장
        await check_length(diary_name, 255, 4023)
        await check_length(content, 1000, 4221)
        now = await time_now()
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

        # 다이어리 반환
        return diary

    async def read(self, diary_id: int) -> NightDiary:

        # 다이어리 조회
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4012,
            )

        # 조회수 증가
        diary.view_count += 1
        diary = save_db(diary, self.db)

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

        if diary_data.diary_name != "":
            await check_length(diary_data.diary_name, 255, 4023)
            diary.diary_name = diary_data.diary_name
        if diary_data.content != "":
            await check_length(diary_data.content, 1000, 4221)
            diary.content = diary_data.content
        diary.modify_date = await time_now()
        diary = save_db(diary, self.db)

        # 다이어리 반환
        return diary

    async def delete(self, diary_id: int) -> None:
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
        save_db(diary, self.db)

    async def list(self, page: int) -> list:

        # 다이어리 조회
        diaries = self.db.query(NightDiary).filter(NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).order_by(NightDiary.create_date.desc()).limit(10).offset((page - 1) * 10).all()
        total_count = self.db.query(NightDiary).filter(NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).count()

        # 각 꿈 객체를 사전 형태로 변환하고 새로운 키-값 쌍 추가
        diaries_dict_list = []
        for diary in diaries:
            diary_dict = diary.__dict__.copy()
            diary_dict.pop('_sa_instance_state', None)
            diary_dict["diary_type"] = 2
            diaries_dict_list.append(diary_dict)

        # 총 개수와 페이지당 개수 정보 추가
        diaries_dict_list.append({"count": 10, "total_count": total_count})

        # 변환된 꿈 리스트 반환
        return diaries_dict_list