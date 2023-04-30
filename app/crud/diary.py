from app.core.current_time import get_current_time
from app.db.database import get_db
from app.db.models.diary import Diary
from app.schemas.request.crud import Create
from fastapi import HTTPException


async def createDiary(create: Create, userId: int, db: get_db()):
    try:
        diary = Diary(
            User_id=userId,
            dream_name=create.dream_name,
            dream=create.dream,
            image_url=create.image_url,
            date=get_current_time(),
        )
        db.add(diary)
        db.commit()
        db.refresh(diary)
    except Exception as e:
        print(e)


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

async def deleteDiary(diaryId: int, userId: int, db: get_db()):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 이미 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    if diary.User_id != userId: # 해당 id의 게시글이 작성자가 아닐 때
        raise HTTPException(status_code=400, detail="You are not the owner of this diary")

    diary.is_deleted = True
    db.commit()
    db.refresh(diary)
