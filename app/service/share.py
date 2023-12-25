from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db, save_db
from app.db.models import MorningDiary, NightDiary
from app.service.abstract import AbstractShareService


class ShareService(AbstractShareService):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def dream_read(self, dream_id: int):

        # dream 조회
        diary = self.db.query(MorningDiary).filter(MorningDiary.id == dream_id, MorningDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4011,
            )

        # 조회수 증가
        diary.share_count += 1
        diary = save_db(diary, self.db)

        # 다이어리 반환
        diary.User_id = None
        return diary

    async def diary_read(self, diary_id: int) -> NightDiary:

        # 다이어리 조회
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4011,
            )

        # 조회수 증가
        diary.share_count += 1
        diary = save_db(diary, self.db)

        # 다이어리 반환
        diary.User_id = None
        return diary