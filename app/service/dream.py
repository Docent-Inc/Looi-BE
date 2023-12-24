import asyncio
import json
from datetime import datetime

from fastapi import Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.security import get_current_user, check_length, time_now
from app.db.database import get_db, save_db, get_redis_client
from app.db.models import User, MorningDiary
from app.core.aiRequset import GPTService
from app.schemas.request import CreateDreamRequest, UpdateDreamRequest
from app.service.abstract import AbstractDiaryService


class DreamService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        self.user = user
        self.db = db

    async def create(self, dream_data: CreateDreamRequest) -> MorningDiary:

        # 사용자의 mbti와 content를 합친 문자열 생성
        content = dream_data.content
        mbti_content = content if self.user.mbti is None else self.user.mbti + ", " + content

        # 다이어리 제목, 이미지, 해몽 생성
        gpt_service = GPTService(self.user, self.db)
        diary_name, image_info, resolution = await asyncio.gather(
            gpt_service.send_gpt_request(2, content),
            gpt_service.send_dalle_request("꿈에서 본 장면: " + content),
            gpt_service.send_gpt_request(5, mbti_content)
        )

        # 이미지 background color 문자열로 변환
        image_url, upper_dominant_color, lower_dominant_color = image_info
        upper_lower_color = "[\"" + str(upper_dominant_color) + "\", \"" + str(lower_dominant_color) + "\"]"

        # db에 저장
        await check_length(diary_name, 255, 4023)
        await check_length(content, 1000, 4221)
        now = await time_now()
        resolution = json.loads(resolution)
        try:
            diary = MorningDiary(
                content=content,
                User_id=self.user.id,
                image_url=image_url,
                background_color=upper_lower_color,
                diary_name=diary_name,
                resolution=resolution['resolution'],
                main_keyword=json.dumps(resolution["main_keywords"], ensure_ascii=False),
                create_date=now,
                modify_date=now,
            )
            diary = save_db(diary, self.db)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4021,
            )

        # 다이어리 반환
        return diary

    async def read(self, diary_id: int) -> MorningDiary:

        # 다이어리 조회
        diary = self.db.query(MorningDiary).filter(MorningDiary.id == diary_id, MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4011,
            )

        # 조회수 증가
        diary.view_count += 1
        diary = save_db(diary, self.db)

        # 다이어리 반환
        return diary

    async def update(self, dream_id: int, dream_data: UpdateDreamRequest) -> MorningDiary:

        # 다이어리 조회
        diary = self.db.query(MorningDiary).filter(MorningDiary.id == dream_id, MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4011,
            )

        # 수정된 사항이 있을 경우 수정
        if dream_data.diary_name != "":
            await check_length(dream_data.diary_name, 255, 4023)
            diary.diary_name = dream_data.diary_name
        if dream_data.content != "":
            await check_length(dream_data.content, 1000, 4221)
            diary.content = dream_data.content

        # 수정된 날짜 저장
        diary.modify_date = await time_now()
        diary = save_db(diary, self.db)

        # list cache 삭제
        redis = await get_redis_client()
        keys = await redis.keys(f"dream:list:{self.user.id}:page:*")
        for key in keys:
            await redis.delete(key)

        # 다이어리 반환
        return diary

    async def delete(self, dream_id: int) -> None:
        redis = await get_redis_client()

        # 다이어리 조회
        diary = self.db.query(MorningDiary).filter(MorningDiary.id == dream_id, MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=4011,
            )

        # 다이어리 삭제
        diary.is_deleted = True
        save_db(diary, self.db)

        # history cache 삭제
        now = await time_now()
        redis_key = f"history:{self.user.id}:{now.day}"
        cached_data = await redis.get(redis_key)
        if cached_data:
            datas = json.loads(cached_data)
            is_exist = False
            for data in datas["MorningDiary"]:
                if data == diary.id:
                    is_exist = True
            for data in datas["MorningDiary"]:
                if data == diary.id:
                    is_exist = True
            if is_exist:
                await redis.delete(redis_key)

        # list cache 삭제
        keys = await redis.keys(f"dream:list:{self.user.id}:page:*")
        for key in keys:
            await redis.delete(key)

    async def list(self, page: int, background_tasks: BackgroundTasks) -> dict:

        async def cache_next_page(page: int, total_count: int) -> None:
            limit, offset = (7, 0) if page == 1 else (8, 7 + (page - 2) * 8)
            dreams = self.db.query(MorningDiary).filter(MorningDiary.User_id == self.user.id,
                                                        MorningDiary.is_deleted == False).order_by(
                MorningDiary.create_date.desc()).limit(limit).offset(offset).all()
            dreams_dict_list = []
            for dream in dreams:
                dream_dict = dream.__dict__.copy()
                dream_dict.pop('_sa_instance_state', None)
                dream_dict["diary_type"] = 1
                dreams_dict_list.append(dream_dict)
            redis = await get_redis_client()
            redis_key = f"dream:list:{self.user.id}:page:{page}"
            await redis.set(redis_key, json.dumps({"list": dreams_dict_list, "count": limit, "total_count": total_count}, default=datetime_serializer), ex=1800)

        def datetime_serializer(o):
            if isinstance(o, datetime):
                return o.isoformat()
            raise TypeError("Object of type '%s' is not JSON serializable" % type(o).__name__)

        # 캐싱된 데이터가 있는지 확인
        redis = await get_redis_client()
        redis_key = f"dream:list:{self.user.id}:page:{page}"
        cached_data = await redis.get(redis_key)


        # 캐싱된 데이터가 있을 경우 캐싱된 데이터 반환 + 다음 페이지 캐싱
        if cached_data:
            json_data = json.loads(cached_data)
            background_tasks.add_task(cache_next_page, page + 1, json_data["total_count"])
            return json_data

        # 캐싱된 데이터가 없을 경우 데이터베이스에서 조회
        limit, offset = (7, 0) if page == 1 else (8, 7 + (page - 2) * 8)
        dreams = self.db.query(MorningDiary).filter(MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).order_by(
            MorningDiary.create_date.desc()).limit(limit).offset(offset).all()

        total_count = self.db.query(MorningDiary).filter(MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).count()


        # 각 꿈 객체를 사전 형태로 변환하고 새로운 키-값 쌍 추가
        dreams_dict_list = []
        for dream in dreams:
            dream_dict = dream.__dict__.copy()
            dream_dict.pop('_sa_instance_state', None)
            dream_dict["diary_type"] = 1
            dreams_dict_list.append(dream_dict)

        # 다음 페이지 캐싱
        background_tasks.add_task(cache_next_page, page + 1, total_count)
        await redis.set(redis_key, json.dumps({"list": dreams_dict_list, "count": limit, "total_count": total_count}, default=datetime_serializer), ex=1800)

        # 다이어리 반환
        return {"list": dreams_dict_list, "count": limit, "total_count": total_count}