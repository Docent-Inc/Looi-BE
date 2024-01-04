import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db, save_db
from app.db.models import MorningDiary, NightDiary, User
from app.service.abstract import AbstractShareService


class ShareService(AbstractShareService):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def dream_link(self, user: User, dream_id: int) -> str:
        dream = self.db.query(MorningDiary).filter(MorningDiary.id == dream_id, MorningDiary.is_deleted == False, MorningDiary.User_id == user.id).first()

        if dream is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4100,
            )

        if dream.is_shared:
            return dream.share_id

        unique_id = str(uuid.uuid4())

        dream.share_id = unique_id
        dream.is_shared = True
        save_db(dream, self.db)

        return unique_id

    async def diary_link(self, user: User, diary_id: int) -> str:
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.is_deleted == False, NightDiary.User_id == user.id).first()

        if diary is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4200,
            )

        if diary.is_shared:
            return diary.share_id
        unique_id = str(uuid.uuid4())

        diary.share_id = unique_id
        diary.is_shared = True
        save_db(diary, self.db)

        return unique_id

    async def read(self, share_id: str) -> object:
        dream = self.db.query(MorningDiary).filter(MorningDiary.share_id == share_id, MorningDiary.is_deleted == False).first()
        if dream is not None:
            dream.share_count += 1
            save_db(dream, self.db)
            return dream

        diary = self.db.query(NightDiary).filter(NightDiary.share_id == share_id, NightDiary.is_deleted == False).first()
        if diary is not None:
            diary.share_count += 1
            save_db(diary, self.db)
            return diary

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=4500,
        )




