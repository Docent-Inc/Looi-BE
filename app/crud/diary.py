from app.core.current_time import get_current_time
from app.db.database import get_db
from app.db.models.diary import Diary
from app.schemas.request.crud import Create, Update
from fastapi import HTTPException


async def createDiary(create: Create, userId: int, db: get_db()):
    try:
        diary = Diary(
            User_id=userId,
            dream_name=create.dream_name,
            dream=create.dream,
            image_url=create.image_url,
            create_date=get_current_time(),
            modify_date=get_current_time(),
        )
        db.add(diary)
        db.commit()
        db.refresh(diary)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def readDiary(diaryId: int, userId: int, db: get_db()):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    # diary 조회수 증가
    diary.view_count += 1
    db.commit()
    db.refresh(diary)

    is_owner = diary.User_id == userId
    if is_owner or diary.is_public:
        return (
            diary.is_public,
            is_owner,
            diary.create_date,
            diary.modify_date,
            diary.image_url,
            diary.view_count,
            diary.like_count,
            diary.dream_name,
            diary.dream,
            diary.is_modified,
        )
    else:
        return (
            False,
            False,
            diary.create_date,
            diary.modify_date,
            diary.image_url,
            diary.view_count,
            diary.like_count,
            None,
            None,
            diary.is_modified,
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

async def updateDiary(diaryId: int, userId: int, create: Update, db: get_db()):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 이미 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    if diary.User_id != userId: # 해당 id의 게시글이 작성자가 아닐 때
        raise HTTPException(status_code=400, detail="You are not the owner of this diary")

    diary.dream_name = create.dream_name
    diary.dream = create.dream
    diary.modify_date = get_current_time()
    diary.is_modified = True
    db.commit()
    db.refresh(diary)