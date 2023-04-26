from app.db.database import get_db
from app.db.models.diary import Diary
from app.schemas.request.crud import Create
import pytz
from datetime import datetime
from fastapi import HTTPException


async def createDiary(create: Create, userId: int, db: get_db()) -> bool:
    try:
        korea_timezone = pytz.timezone("Asia/Seoul")
        korea_time = datetime.now(korea_timezone)
        formatted_time = korea_time.strftime("%Y%m%d%H%M%S")
        diary = Diary(
            User_id=userId,
            dream_name=create.dream_name,
            dream=create.dream,
            image_url=create.image_url,
            date=formatted_time
        )
        db.add(diary)
        db.commit()
        db.refresh(diary)
        return True
    except Exception as e:
        print(e)
        return False


async def readDiary(diaryId: int, userId: int, db: get_db()):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    is_owner = diary.User_id == userId
    if is_owner or diary.is_public:
        return (
            diary.is_public,
            is_owner,
            diary.date,
            diary.image_url,
            diary.view_count,
            diary.like_count,
            diary.dream_name,
            diary.dream
        )
    else:
        return (
            False,
            False,
            diary.date,
            diary.image_url,
            diary.view_count,
            diary.like_count,
            None,
            None
        )

