import asyncio
import json
import aioredis
from fastapi import Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.security import get_current_user, check_length, time_now, datetime_serializer, diary_serializer
from app.db.database import get_db, save_db, get_redis_client
from app.db.models import User, NightDiary
from app.core.aiRequset import GPTService
from app.schemas.request import CreateDiaryRequest
from app.service.abstract import AbstractDiaryService
from app.service.push import PushService


class DiaryService(AbstractDiaryService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db), redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def create(self, diary_data: CreateDiaryRequest) -> NightDiary:

        diary_name = ""
        if diary_data.diary_name != "":
            await check_length(diary_data.diary_name, 255, 4023)
            diary_name = diary_data.diary_name

        now = await time_now()
        if diary_data.date == "" or str(diary_data.date[:10]) == str(now.date()):
            diary_data.date = now

        await check_length(diary_data.content, 1000, 4221)
        diary = NightDiary(
            content=diary_data.content,
            User_id=self.user.id,
            image_url="",
            background_color="",
            resolution="",
            main_keyword="",
            diary_name=diary_name,
            create_date=diary_data.date,
            modify_date=now,
        )
        diary = save_db(diary, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"diary:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # 새로운 cache 생성
        redis_key = f"diary:{self.user.id}:{diary.id}"
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        # ratio cache 삭제
        redis_key = f"statistics:ratio:{self.user.id}"
        await self.redis.delete(redis_key)

        # 다이어리 반환
        return diary

    async def generate(self, diary_id: int, background_tasks: BackgroundTasks) -> dict:

        # 다이어리 조회
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id,
                                                 NightDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=4200)

        if diary.is_generated:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=4201)

        gpt_service = GPTService(self.user, self.db)
        if diary.diary_name == "":
            image_url, diary_name, reply = await asyncio.gather(
                gpt_service.send_dalle_request(f"오늘의 일기(no text): {diary.content}"),
                gpt_service.send_gpt_request(2, diary.content),
                gpt_service.send_gpt_request(10, diary.content)
            )
            await check_length(diary_name, 255, 4023)
            diary.diary_name = diary_name

        elif diary.diary_name != "":
            image_url, reply = await asyncio.gather(
                gpt_service.send_dalle_request(f"오늘의 일기(no text): {diary.content}"),
                gpt_service.send_gpt_request(10, diary.content)
            )

        try:
            diary.image_url = image_url
            diary.resolution = json.loads(reply)["reply"]
            diary.main_keyword = json.dumps(json.loads(reply)["main_keywords"], ensure_ascii=False)
            diary.is_generated = True
            diary.modify_date = await time_now()
            diary = save_db(diary, self.db)
            push_service = PushService(db=self.db, user=self.user)
            background_tasks.add_task(
                push_service.send,
                "Looi",
                f"{self.user.nickname}님의 일기에 대한 답장이 도착했어요! 얼른 확인해 보세요~!",
                self.user.push_token
            )
        except:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=4202)

        # list cache 삭제
        keys = await self.redis.keys(f"diary:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # 새로운 cache 생성
        redis_key = f"diary:{self.user.id}:{diary.id}"
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        return {"diary": diary}

    async def read(self, diary_id: int, background_tasks: BackgroundTasks) -> NightDiary:

        async def count_view(diary_id: int) -> None:
            diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).first()
            diary.view_count += 1
            save_db(diary, self.db)

        # 캐싱된 데이터가 있는지 확인
        redis_key = f"diary:{self.user.id}:{diary_id}"
        redis_data = await self.redis.get(redis_key)
        if redis_data:
            background_tasks.add_task(count_view, diary_id)
            return json.loads(redis_data)

        # 다이어리 조회
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=4200)

        # 데이터 캐싱
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        # 다이어리 반환
        return diary



    async def update(self, diary_id: int, diary_data: CreateDiaryRequest) -> NightDiary:
        # 다이어리 조회
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=4200)

        if diary_data.diary_name != "":
            await check_length(diary_data.diary_name, 255, 4023)
            diary.diary_name = diary_data.diary_name
        if diary_data.content != "":
            await check_length(diary_data.content, 1000, 4221)
            diary.content = diary_data.content
        diary.modify_date = await time_now()
        diary = save_db(diary, self.db)

        # list cache 삭제
        keys = await self.redis.keys(f"diary:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # diary cache
        redis_key = f"diary:{self.user.id}:{diary_id}"
        await self.redis.set(redis_key, json.dumps(diary, default=diary_serializer, ensure_ascii=False), ex=1800)

        # 다이어리 반환
        return diary

    async def delete(self, diary_id: int) -> None:
        redis = await get_redis_client()
        # 다이어리 조회
        diary = self.db.query(NightDiary).filter(NightDiary.id == diary_id, NightDiary.User_id == self.user.id, NightDiary.is_deleted == False).first()

        # 다이어리가 없을 경우 예외 처리
        if not diary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=4200)
        # 다이어리 삭제
        diary.is_deleted = True
        diary = save_db(diary, self.db)

        # history cache 삭제
        now = await time_now()
        redis_key = f"history:{self.user.id}:{now.day}"
        cached_data = await redis.get(redis_key)
        if cached_data:
            datas = json.loads(cached_data)
            is_exist = False
            for data in datas["NightDiary"]:
                if data == diary.id:
                    is_exist = True
            for data in datas["NightDiary"]:
                if data == diary.id:
                    is_exist = True
            if is_exist:
                await redis.delete(redis_key)

        # list cache 삭제
        keys = await self.redis.keys(f"diary:list:{self.user.id}:*")
        for key in keys:
            await self.redis.delete(key)

        # diary cache 삭제
        await redis.delete(f"diary:{self.user.id}:{diary.id}")

        # ratio cache 삭제
        redis_key = f"statistics:ratio:{self.user.id}"
        await self.redis.delete(redis_key)

    async def list(self, page: int, background_tasks: BackgroundTasks) -> dict:

        async def cache_next_page(page: int, total_count: int) -> None:
            limit, offset = (7, 0) if page == 1 else (8, 7 + (page - 2) * 8)
            diaries = self.db.query(NightDiary).filter(NightDiary.User_id == self.user.id,
                                                        NightDiary.is_deleted == False).order_by(
                NightDiary.create_date.desc()).limit(limit).offset(offset).all()
            diaries_dict_list = []
            for diary in diaries:
                diary_dict = diary.__dict__.copy()
                diary_dict.pop('_sa_instance_state', None)
                diary_dict["diary_type"] = 2
                diaries_dict_list.append(diary_dict)
            redis_key = f"diary:list:{self.user.id}:{page}"
            await self.redis.set(redis_key,
                            json.dumps({"list": diaries_dict_list, "count": limit, "total_count": total_count},
                                       default=str, ensure_ascii=False), ex=1800)

        # 캐싱된 데이터가 있는지 확인
        redis_key = f"diary:list:{self.user.id}:{page}"
        cached_data = await self.redis.get(redis_key)

        # 캐싱된 데이터가 있을 경우 캐싱된 데이터 반환 + 다음 페이지 캐싱
        if cached_data:
            json_data = json.loads(cached_data)
            background_tasks.add_task(cache_next_page, page + 1, json_data["total_count"])
            return json_data

        # 캐싱된 데이터가 없을 경우 데이터베이스에서 조회
        limit, offset = (7, 0) if page == 1 else (8, 7 + (page - 2) * 8)
        diaries = self.db.query(NightDiary).filter(NightDiary.User_id == self.user.id,
                                                    NightDiary.is_deleted == False).order_by(
            NightDiary.create_date.desc()).limit(limit).offset(offset).all()

        total_count = self.db.query(NightDiary).filter(NightDiary.User_id == self.user.id,
                                                         NightDiary.is_deleted == False).count()

        # 각 꿈 객체를 사전 형태로 변환하고 새로운 키-값 쌍 추가
        diaries_dict_list = []
        for diary in diaries:
            diary_dict = diary.__dict__.copy()
            diary_dict.pop('_sa_instance_state', None)
            diary_dict["diary_type"] = 2
            diaries_dict_list.append(diary_dict)

        # 다음 페이지 캐싱
        background_tasks.add_task(cache_next_page, page + 1, total_count)
        await self.redis.set(redis_key, json.dumps({"list": diaries_dict_list, "count": limit, "total_count": total_count},
                                              default=str, ensure_ascii=False), ex=1800)

        # 다이어리 반환
        return {"list": diaries_dict_list, "count": limit, "total_count": total_count}