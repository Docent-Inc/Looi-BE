from fastapi import HTTPException

from app.db.models.diary import Diary
from app.db.models.hot import Hot
from sqlalchemy import func
from sqlalchemy.sql.expression import or_
from sqlalchemy.orm import Session
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

async def listHot(page: int, db: Session):
    try:
        # Hot 테이블에서 모든 요소를 불러온 후 같은 diaryId를 가진 요소들의 weight를 합산합니다.
        # 그 후, weight를 기준으로 내림차순 정렬합니다.
        # 마지막으로, 페이지네이션을 적용합니다.
        hot_list = (
            db.query(
                Hot.Diary_id,
                func.sum(Hot.weight).label("total_weight"),
            )
            .group_by(Hot.Diary_id)
            .order_by(func.sum(Hot.weight).desc())
            .limit(10)
            .offset((page - 1) * 10)
            .all()
        )

        # hot_list를 반환합니다.
        return hot_list
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
            .offset((page - 1) * 10)
            .limit(10)
            .all()
        )
        return diaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

