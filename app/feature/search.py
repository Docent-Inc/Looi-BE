from fastapi import HTTPException
from sqlalchemy.orm import joinedload
from app.db.models.diary import Diary
from app.db.models.hot import Hot
from app.db.models.search import SearchHistory
from app.db.models.user import User
from sqlalchemy import func, desc
from sqlalchemy.sql.expression import or_
from sqlalchemy.orm import Session
from app.schemas.response.diary import DiaryIamgeListResponse


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
            .join(Diary, Diary.id == Hot.Diary_id)
            .filter(Diary.is_deleted == False)
            .group_by(Hot.Diary_id)
            .order_by(func.sum(Hot.weight).desc())
            .limit(18)
            .offset((page - 1) * 18)
            .all()
        )

        diary_list_response = []
        for hot_item in hot_list:
            diary_id, total_weight = hot_item
            diary = db.query(Diary).options(joinedload(Diary.user)).filter(Diary.id == diary_id).first()

            diary_response = DiaryIamgeListResponse(
                id=diary.id,
                image_url=diary.image_url,
            )
            diary_list_response.append(diary_response)

        return diary_list_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def listText(page: int, text: str, db: Session, user_id: int):
    try:
        diaries = (
            db.query(Diary)
            .options(joinedload(Diary.user))
            .filter(
                or_(
                    Diary.dream_name.ilike(f"%{text}%"),
                    Diary.dream.ilike(f"%{text}%")
                ),
                Diary.is_deleted == False
            )
            .offset((page - 1) * 18)
            .limit(18)
            .all()
        )

        diary_list_response = []
        for diary in diaries:
            diary_response = DiaryIamgeListResponse(
                id=diary.id,
                image_url=diary.image_url,
            )
            diary_list_response.append(diary_response)

        # 사용자 ID와 검색어로 기존 검색 기록을 조회
        existing_search_history = db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id,
            SearchHistory.search_term == text
        ).first()

        # 기존 검색 기록이 없는 경우만 새 검색 기록을 추가
        if existing_search_history is None:
            new_search_history = SearchHistory(user_id=user_id, search_term=text)
            db.add(new_search_history)
            db.commit()

        return diary_list_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def listSearchHistory(user_id: int, db: Session):
    search_history = db.query(SearchHistory).filter(SearchHistory.user_id == user_id).order_by(
        desc(SearchHistory.search_timestamp)).all()
    return search_history

async def deleteSearchHistory(id, user_id: int, db: Session):
    try:
        search_history = db.query(SearchHistory).filter(SearchHistory.id == id, SearchHistory.user_id == user_id).first()
        if search_history:
            db.delete(search_history)
            db.commit()
            return True
        else:
            return False
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def deleteSearchHistoryAll(user_id: int, db: Session):
    try:
        search_history = db.query(SearchHistory).filter(SearchHistory.user_id == user_id).all()
        if search_history:
            for history in search_history:
                db.delete(history)
            db.commit()
            return True
        else:
            return False
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))