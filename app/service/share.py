from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db, save_db
from app.db.models import MorningDiary, NightDiary
from app.service.abstract import AbstractShareService


class ShareService(AbstractShareService):
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

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




