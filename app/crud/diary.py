from app.core.current_time import get_current_time
from app.crud.hot import maintain_hot_table_limit
from app.db.database import get_db
from app.db.models.diary import Diary
from app.db.models.hot import Hot
from app.db.models.like import Like
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
    except:
        raise HTTPException(status_code=500, detail="데이터베이스에 오류가 발생했습니다.")


async def readDiary(diaryId: int, userId: int, db: get_db()):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    try:
        diary.view_count += 1
        db.commit()
        db.refresh(diary)
    except:
        raise HTTPException(status_code=500, detail="데이터베이스에 오류가 발생했습니다.")

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

    try:
        diary.is_deleted = True
        db.commit()
        db.refresh(diary)
    except:
        raise HTTPException(status_code=500, detail="데이터베이스에 오류가 발생했습니다.")

async def updateDiary(diaryId: int, userId: int, create: Update, db: get_db()):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()
    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 이미 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    if diary.User_id != userId: # 해당 id의 게시글이 작성자가 아닐 때
        raise HTTPException(status_code=400, detail="You are not the owner of this diary")
    try:
        diary.dream_name = create.dream_name
        diary.dream = create.dream
        diary.modify_date = get_current_time()
        diary.is_modified = True
        db.commit()
        db.refresh(diary)
    except:
        raise HTTPException(status_code=500, detail="데이터베이스에 오류가 발생했습니다.")

async def likeDiary(diaryId: int, userId: int, db: get_db()):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()
    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 이미 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    # like 테이블에 이미 있다면 좋아요 안됨
    if db.query(Like).filter(Like.Diary_id == diaryId, Like.User_id == userId).first() is not None:
        raise HTTPException(status_code=400, detail="Already liked")

    try:
        diary.like_count += 1
        db.commit()
        db.refresh(diary)

        # like 테이블에 추가
        like = Like(
            User_id=userId,
            Diary_id=diaryId
        )
        db.add(like)
        db.commit()
        db.refresh(like)

        # 가장 오래된 데이터의 id를 사용하거나, 그렇지 않으면 가장 큰 id에 1을 더합니다.
        # Hot 테이블에 추가하기 전에 데이터 제한을 확인하고 관리합니다.
        oldest_index = await maintain_hot_table_limit(db)
        if oldest_index is None:
            first_hot = db.query(Hot).order_by(Hot.id.desc()).first()
            if first_hot is None:
                max_index = 0
            else:
                max_index = first_hot.index
            new_index = max_index + 1
        else:
            new_index = oldest_index

        # Hot 테이블에 가중치 추가
        existing_hot = db.query(Hot).filter(Hot.Diary_id == diaryId, Hot.User_id == userId, Hot.weight == 3).first()
        if existing_hot is None:
            hot = Hot(
                index=new_index,
                weight=3,  # 좋아요 가중치
                Diary_id=diaryId,
                User_id=userId
            )
            db.add(hot)
            db.commit()
            db.refresh(hot)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def unlikeDiary(diaryId: int, userId: int, db: get_db()):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 이미 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    try:
        diary.like_count -= 1
        db.commit()
        db.refresh(diary)

        # like 테이블에서 삭제
        like = db.query(Like).filter(Like.User_id == userId, Like.Diary_id == diaryId).first()
        if like is None:
            raise HTTPException(status_code=404, detail="Like not found")
        db.delete(like)
        db.commit()
    except:
        raise HTTPException(status_code=500, detail="데이터베이스에 오류가 발생했습니다.")
