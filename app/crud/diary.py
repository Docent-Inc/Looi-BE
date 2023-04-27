from app.db.database import get_db
from app.db.models.diary import Diary
from app.schemas.request.crud import Create
import pytz
from datetime import datetime

async def createDiary(create: Create, userId: int, db: get_db()) -> bool:
    try:
        korea_timezone = pytz.timezone("Asia/Seoul")
        korea_time = datetime.now(korea_timezone)
        formatted_time = korea_time.strftime("%Y%m%d%H%M%S")
        diary = Diary(
            User_id=userId,
            dream_name=create.dream_name,
            dream=create.dream,
            date=formatted_time
        )
        db.add(diary)
        db.commit()
        db.refresh(diary)
        return True
    except Exception as e:
        print(e)
        return False
