from fastapi import HTTPException
from app.db.models.hot import Hot
async def maintain_hot_table_limit(db):
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