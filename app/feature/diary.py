from sqlalchemy import func

from app.core.current_time import get_current_time
from app.db.models import User
from app.db.models.diary_en import Diary_en
from app.db.models.diary_ko import Diary_ko
from app.feature.search import maintain_hot_table_limit
from app.db.models.comment import Comment
from app.db.models.diary import Diary
from app.db.models.hot import Hot
from app.db.models.like import Like
from app.schemas.request.crud import Create, Update, commentRequest
from fastapi import HTTPException
from sqlalchemy.orm import Session

async def createDiary(create: Create, userId: int, db: Session):
    try:
        user = db.query(User).filter(User.id == userId).first()
        diary = Diary(
            User_id=userId,
            checklist=create.checklist,
            image_url=create.image_url,
            create_date=get_current_time(),
            modify_date=get_current_time(),
            is_public=create.is_public,
        )
        db.add(diary)
        db.commit()
        db.refresh(diary)

        diary_content = Diary_ko(
            Diary_id=diary.id,
            dream_name=create.dream_name,
            dream=create.dream,
            resolution=create.resolution,
        )
        db.add(diary_content)
        db.commit()
        db.refresh(diary_content)

        if user.language_id == 2:
            diary_content = Diary_en(
                Diary_id=diary.id,
                dream_name=create.dream_name,
                dream=create.dream,
                resolution=create.resolution,
            )
            db.add(diary_content)
            db.commit()
            db.refresh(diary_content)
        return diary.id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def readDiary(diaryId: int, userId: int, db: Session):
    user = db.query(User).filter(User.id == userId).first()
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    diary_content = db.query(Diary_ko).filter(Diary_ko.Diary_id == diaryId).first()
    if user.language_id == 2: # 영어
        diary_content = db.query(Diary_ko).filter(Diary_ko.Diary_id == diaryId).first()


    try:
        diary.view_count += 1
        db.commit()
        db.refresh(diary)

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
        existing_hot = db.query(Hot).filter(Hot.Diary_id == diaryId, Hot.User_id == userId, Hot.weight == 1).first()
        if existing_hot is None:
            hot = Hot(
                index=new_index,
                weight=1,  # 좋아요 가중치
                Diary_id=diaryId,
                User_id=userId
            )
            db.add(hot)
            db.commit()
            db.refresh(hot)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    is_owner = diary.User_id == userId
    is_liked = db.query(Like).filter(Like.Diary_id == diaryId, Like.User_id == userId).first() is not None
    if is_owner or diary.is_public:
        return (
            diary.is_public,
            is_owner,
            diary.create_date,
            diary.modify_date,
            diary.image_url,
            diary.view_count,
            diary.like_count,
            diary_content.dream_name,
            diary_content.dream,
            diary_content.resolution,
            diary.checklist,
            diary.is_modified,
            diary.comment_count,
            is_liked,
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
            diary_content.dream_name,
            "",  # 빈 문자열로 기본값 설정
            "",
            "",
            diary.is_modified,
            diary.comment_count,
            is_liked,
        )

async def deleteDiary(diaryId: int, userId: int, db: Session):
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def updateDiary(diaryId: int, userId: int, create: Update, db: Session):
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def likeDiary(diaryId: int, userId: int, db: Session):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()
    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 이미 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    # like 테이블에 이미 있다면 좋아요 안됨
    if db.query(Like).filter(Like.Diary_id == diaryId, Like.User_id == userId).first() is not None:
        raise HTTPException(status_code=400, detail="Already liked")

    try:
        diary.like_count += 1 # 좋아요 수 증가
        # like 테이블에 추가
        like = Like(
            User_id=userId,
            Diary_id=diaryId
        )
        db.add(like)
        db.commit()
        db.refresh(like)
        db.refresh(diary)

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

async def unlikeDiary(diaryId: int, userId: int, db: Session):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 이미 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    try:
        diary.like_count -= 1
        db.commit()
        db.refresh(diary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # like 테이블에서 삭제
    like = db.query(Like).filter(Like.User_id == userId, Like.Diary_id == diaryId).first()
    try:
        if like is None:
            raise HTTPException(status_code=404, detail="Like not found")
        db.delete(like)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def commentDiary(diaryId: int, userId: int, create: commentRequest, db: Session):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 이미 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    try:
        comment = Comment(
            comment=create.comment,
            User_id=userId,
            Diary_id=diaryId,
            create_date=get_current_time()
        )

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
        existing_hot = db.query(Hot).filter(Hot.Diary_id == diaryId, Hot.User_id == userId, Hot.weight == 5).first()
        if existing_hot is None:
            hot = Hot(
                index=new_index,
                weight=5,  # 댓글 가중치
                Diary_id=diaryId,
                User_id=userId
            )
            db.add(hot)
            db.commit()
            db.refresh(hot)
        diary.comment_count += 1
        db.add(comment)
        db.commit()
        db.refresh(comment)

        return comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def uncommentDiary(diaryId: int, commentId: int, db: Session):
    diary = db.query(Diary).filter(Diary.id == diaryId).first()

    if diary is None: # 해당 id의 게시글이 없을 때
        raise HTTPException(status_code=404, detail="Diary not found")

    if diary.is_deleted: # 해당 id의 게시글이 이미 삭제되었을 때
        raise HTTPException(status_code=400, detail="Diary has been deleted")

    comment = db.query(Comment).filter(Comment.id == commentId, Comment.is_deleted == False).first()
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    try:
        comment.is_deleted = True
        diary.comment_count -= 1
        db.commit()
        db.refresh(comment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def listDiary(page: int, id: int , db: Session):
    try:
        diary = db.query(Diary).filter(Diary.is_deleted == False).order_by(Diary.create_date.desc()).limit(5).offset((page-1)*5).all()
        for i in range(len(diary)):
            diary[i].User = db.query(User).filter(User.id == diary[i].User_id).first()
        for i in range(len(diary)):
            diary[i].nickname = diary[i].User.nickName
            diary[i].userId = diary[i].User.id
            # 현재 사용자가 좋아요를 눌렀는지 확인하여 is_liked를 추가합니다.
            is_liked = db.query(Like).filter(Like.Diary_id == diary[i].id, Like.User_id == id).first() is not None
            diary[i].is_liked = is_liked
        return diary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def listDiaryByUser(user_id: int, page: int, currentUser_id: int, db: Session):
    try:
        diary = db.query(Diary).filter(Diary.User_id == user_id, Diary.is_deleted == False).order_by(Diary.create_date.desc()).limit(9).offset((page-1)*9).all()
        for i in range(len(diary)):
            diary[i].User = db.query(User).filter(User.id == diary[i].User_id).first()
        for i in range(len(diary)):
            diary[i].nickname = diary[i].User.nickName
            diary[i].userId = diary[i].User.id
            if diary[i].User_id == currentUser_id:
                diary[i].isMine = True
            else:
                diary[i].isMine = False
            # 현재 사용자가 좋아요를 눌렀는지 확인하여 is_liked를 추가합니다.
            is_liked = db.query(Like).filter(Like.Diary_id == diary[i].id, Like.User_id == currentUser_id).first() is not None
            diary[i].is_liked = is_liked
        return diary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def listComment(userId: int, diaryId: int, page: int, db: Session):
    try:
        comments = db.query(Comment).filter(Comment.Diary_id == diaryId, Comment.is_deleted == False).order_by(Comment.create_date.asc()).limit(10).offset((page-1)*10).all()
        for i in range(len(comments)):
            user = db.query(User).filter(User.id == comments[i].User_id).first()
            comments[i].nickname = user.nickName
            comments[i].userId = user.id
            # 댓글이 내 것인지 확인
            comments[i].is_mine = True if userId == comments[i].User_id else False
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def updateDiaryIsPublic(diaryId: int, userId: int, isPublic: bool, db: Session):
    diary = db.query(Diary).filter(Diary.id == diaryId, Diary.User_id == userId).first()
    if diary is None:
        raise HTTPException(status_code=404, detail="Diary not found")
    try:
        diary.is_public = isPublic
        db.commit()
        db.refresh(diary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def randomDiary(db: Session):
    try:
        # 랜덤 다이어리를 불러옵니다
        diary = db.query(Diary).filter(Diary.is_deleted == False).order_by(func.random()).first()
        return diary.id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def readDiaryCount(db: Session):
    try:
        diary = db.query(Diary).count() + 339 # 1차 테스트 데이터 339개
        return diary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))