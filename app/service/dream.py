import asyncio
import json
import random
import uuid

import aioredis
from fastapi import Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.security import get_current_user, check_length, time_now, diary_serializer
from app.db.database import get_db, save_db, get_redis_client
from app.db.models import User, MorningDiary, NightDiary
from app.core.aiRequset import GPTService
from app.schemas.request import CreateDreamRequest, UpdateDreamRequest
from app.service.abstract import AbstractDiaryService
from app.service.push import PushService


class DreamService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db), redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def create(self, dream_data: CreateDreamRequest) -> MorningDiary:

        # db에 저장
        await check_length(dream_data.content, 1000, 4221)
        now = await time_now()
        diary_name = f"{now.year}년 {now.month}월 {now.day}일의 꿈"
        try:
            diary = MorningDiary(
                content=dream_data.content,
                User_id=self.user.id,
                image_url="",
                diary_name=diary_name,
                resolution="",
                share_id=str(uuid.uuid4()),
                main_keyword="",
                create_date=now,
                modify_date=now,
            )
            diary = save_db(diary, self.db)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4021,
            )

        # list cache 삭제
        keys = await self.redis.keys(f"dream:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # 새로운 cache 생성
        redis_key = f"dream:{self.user.id}:{diary.id}"
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        # ratio cache 삭제
        redis_key = f"statistics:ratio:{self.user.id}"
        await self.redis.delete(redis_key)

        # 다이어리 반환
        return diary

    async def generate(self, dream_id: int, background_tasks) -> dict:

        # 다이어리 조회
        diary = self.db.query(MorningDiary).filter(MorningDiary.id == dream_id, MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).first()

        # 꿈이 없을 경우 예외 처리
        if not diary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=4100)

        if diary.is_generated == True:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=4102)

        # 다이어리 제목, 이미지, 해몽 생성
        gpt_service = GPTService(self.user, self.db)
        diary_name, image_url, resolution = await asyncio.gather(
            gpt_service.send_gpt_request(2, diary.content),
            gpt_service.send_dalle_request(f"꿈에서 본 장면(no text, digital art, illustration): {diary.content}"),
            gpt_service.send_gpt_request(5, f"nickname: {self.user.nickname}, mbti: {self.user.mbti}, dream: {diary.content}")
        )

        # db에 저장
        if diary.diary_name == "":
            diary.diary_name = diary_name[:20]

        try:
            diary.image_url = image_url
            diary.resolution = json.loads(resolution)['resolution']
            diary.main_keyword = json.dumps(json.loads(resolution)["main_keywords"], ensure_ascii=False)
            diary.modify_date = await time_now()
            diary.is_generated = True
            diary = save_db(diary, self.db)
            push_service = PushService(db=self.db, user=self.user)
            background_tasks.add_task(
                push_service.send,
                title="Looi",
                body=f"{self.user.nickname}님의 꿈 해석 결과가 도착했어요 💭",
                device=f"{self.user.device}",
                image_url=diary.image_url,
                landing_url=f"/diary/{diary.id}?type=1",
                token=self.user.push_token
            )
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=4101,
            )

        # list cache 삭제
        keys = await self.redis.keys(f"dream:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # 새로운 cache 생성
        redis_key = f"dream:{self.user.id}:{diary.id}"
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        return {"diary": diary}

    async def read(self, dream_id: int, background_tasks: BackgroundTasks) -> MorningDiary:
        async def count_view(dream_id: int) -> None:
            diary = self.db.query(MorningDiary).filter(MorningDiary.id == dream_id, MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).first()
            diary.view_count += 1
            save_db(diary, self.db)

        # 캐시된 데이터가 있는지 확인
        redis_key = f"dream:{self.user.id}:{dream_id}"
        cached_data = await self.redis.get(redis_key)
        if cached_data:
            background_tasks.add_task(count_view, dream_id)
            return json.loads(cached_data)

        # 꿈 조회
        diary = self.db.query(MorningDiary).filter(MorningDiary.id == dream_id, MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).first()

        # 꿈이 없을 경우 예외 처리
        if not diary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=4100)

        # 데이터 캐싱
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        # 다이어리 반환
        return diary

    async def update(self, dream_id: int, dream_data: UpdateDreamRequest) -> MorningDiary:

        # 다이어리 조회
        diary = self.db.query(MorningDiary).filter(MorningDiary.id == dream_id, MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=4100)

        # 수정된 사항이 있을 경우 수정
        if dream_data.diary_name != "":
            await check_length(dream_data.diary_name, 255, 4023)
            diary.diary_name = dream_data.diary_name
        if dream_data.content != "":
            await check_length(dream_data.content, 1000, 4221)
            diary.content = dream_data.content
        try:
            diary.is_like = dream_data.is_like
        except:
            pass
        # 수정된 날짜 저장
        diary.modify_date = await time_now()
        diary = save_db(diary, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"dream:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # 새로운 cache 생성
        redis_key = f"dream:{self.user.id}:{diary.id}"
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        # 다이어리 반환
        return diary

    async def delete(self, dream_id: int) -> None:

        # 다이어리 조회
        diary = self.db.query(MorningDiary).filter(MorningDiary.id == dream_id, MorningDiary.User_id == self.user.id, MorningDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=4100)

        # 다이어리 삭제
        diary.is_deleted = True
        save_db(diary, self.db)

        # history cache 삭제
        now = await time_now()
        redis_key = f"history:{self.user.id}:{now.day}"
        cached_data = await self.redis.get(redis_key)
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
                await self.redis.delete(redis_key)

        # list cache 삭제
        keys = await self.redis.keys(f"dream:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # dream cache 삭제
        redis_key = f"dream:{self.user.id}:{dream_id}"
        await self.redis.delete(redis_key)

        # ratio cache 삭제
        redis_key = f"statistics:ratio:{self.user.id}"
        await self.redis.delete(redis_key)

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
            redis_key = f"dream:list:{self.user.id}:{page}"
            await self.redis.set(redis_key, json.dumps({"list": dreams_dict_list, "count": limit, "total_count": total_count}, default=str, ensure_ascii=False), ex=1800)

        # 캐싱된 데이터가 있는지 확인
        redis_key = f"dream:list:{self.user.id}:{page}"
        cached_data = await self.redis.get(redis_key)


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
        await self.redis.set(redis_key, json.dumps({"list": dreams_dict_list, "count": limit, "total_count": total_count}, default=str, ensure_ascii=False), ex=1800)

        # 다이어리 반환
        return {"list": dreams_dict_list, "count": limit, "total_count": total_count}