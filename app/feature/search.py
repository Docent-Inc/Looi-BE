from fastapi import HTTPException
from sqlalchemy.orm import joinedload
from app.db.models.diary import Diary
from app.db.models.hot import Hot
from app.db.models.like import Like
from app.db.models.user import User
from sqlalchemy import func
from sqlalchemy.sql.expression import or_
from sqlalchemy.orm import Session

from app.schemas.response.diary import DiaryListResponse


async def maintain_hot_table_limit(db: Session):
    hot_data_count = db.query(Hot).count()
    if hot_data_count >= 1000:
        # 가장 오래된 데이터를 찾습니다.
        oldest_hot = db.query(Hot).order_by(Hot.id).first()
        try:
            if oldest_hot:
                # 가장 오래된 데이터를 삭제합니다.
                db.delete(oldest_hot)
                db.commit()
                return oldest_hot.id  # 가장 오래된 데이터의 id를 반환합니다.
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return None # 삭제할 데이터가 없을 경우 None을 반환합니다.



async def listHot(page: int, db: Session, current_user: User):
    try:
        hot_list = (
            db.query(
                Hot.Diary_id,
                func.sum(Hot.weight).label("total_weight"),
            )
            .group_by(Hot.Diary_id)
            .order_by(func.sum(Hot.weight).desc())
            .limit(5)
            .offset((page - 1) * 5)
            .all()
        )

        diary_list_response = []
        for hot_item in hot_list:
            diary_id, total_weight = hot_item
            diary = db.query(Diary).options(joinedload(Diary.user)).filter(Diary.id == diary_id, Diary.is_deleted == False).first()
            if diary is None:
                continue

            user_nickname = diary.user.nickName if diary.user else None

            like = db.query(Like).filter(Like.User_id == current_user.id, Like.Diary_id == diary.id).first()
            is_liked = True if like else False

            diary_response = DiaryListResponse(
                id=diary.id,
                dream_name=diary.dream_name,
                image_url=diary.image_url,
                view_count=diary.view_count,
                like_count=diary.like_count,
                comment_count=diary.comment_count,
                userNickname=user_nickname,
                userId=diary.User_id,
                is_liked=is_liked
            )
            diary_list_response.append(diary_response)

        return diary_list_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def listText(page: int, text: str, db: Session):
    try:
        # Diary 테이블에서 dream_name 또는 dream에 text가 포함된 요소들을 불러옵니다.
        diaries = (
            db.query(Diary)
            .filter(
                or_(
                    Diary.dream_name.ilike(f"%{text}%"),
                    Diary.dream.ilike(f"%{text}%")
                ),
                Diary.is_deleted == False
            )
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )
        return diaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

