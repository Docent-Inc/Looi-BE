from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import User, MorningDiary, NightDiary, Memo
from app.service.abstract import AbstractStatisticsService


class StatisticsService(AbstractStatisticsService):
    def __init__(self, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
        self.db = db
        self.user = user
    async def ratio(self) -> dict:
        MorningDiary_count = self.db.query(MorningDiary).filter(MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).count()
        NightDiary_count = self.db.query(NightDiary).filter(NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).count()
        Memo_count = self.db.query(Memo).filter(Memo.User_id == self.user.id, Memo.is_deleted == False).count()

        total = MorningDiary_count + NightDiary_count + Memo_count
        if total == 0:
            morning_diary_ratio = 0
            night_diary_ratio = 0
            memo_ratio = 0
            max_category = 0
        else:
            morning_diary_ratio = (MorningDiary_count / total) * 100
            night_diary_ratio = (NightDiary_count / total) * 100
            memo_ratio = (Memo_count / total) * 100

        max_category_value = max(morning_diary_ratio, night_diary_ratio, memo_ratio)
        if total == 0:
            pass
        elif morning_diary_ratio == night_diary_ratio and night_diary_ratio == memo_ratio:
            max_category = 4
        elif max_category_value == morning_diary_ratio:
            max_category = 1
        elif max_category_value == night_diary_ratio:
            max_category = 2
        elif max_category_value == memo_ratio:
            max_category = 3

        return {
            "max_category": max_category,
            "morning_diary_count": MorningDiary_count,
            "night_diary_count": NightDiary_count,
            "memo_count": Memo_count,
            "morning_diary_ratio": morning_diary_ratio,
            "night_diary_ratio": night_diary_ratio,
            "memo_ratio": memo_ratio,
        }