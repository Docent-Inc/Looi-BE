from datetime import timedelta
import datetime
import json
import math
from random import randint
import aioredis
import pytz
import requests
from fastapi import Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.aiRequset import GPTService
from app.core.config import settings
from app.core.security import get_current_user, time_now, diary_serializer
from app.db.database import get_db, get_redis_client, save_db
from app.db.models import User, MorningDiary, Luck, NightDiary, Calendar
from app.service.abstract import AbstractTodayService


class TodayService(AbstractTodayService):
    def __init__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db),
                 redis: aioredis.Redis = Depends(get_redis_client)):
        self.user = user
        self.db = db
        self.redis = redis

    async def luck(self) -> dict:
        now = await time_now()
        cached_luck = self.db.query(Luck).filter(
            Luck.User_id == self.user.id,
            Luck.create_date == now.date(),
            Luck.is_deleted == False
        ).first()

        if cached_luck:
            return {"luck": cached_luck.content, "isCheckedToday": True}

        text = ""
        morning = self.db.query(MorningDiary).filter(
            MorningDiary.User_id == self.user.id,
            MorningDiary.create_date >= now.date() - timedelta(days=1),
            MorningDiary.is_deleted == False
        ).first()
        if not morning:
            text = "x"
        else:
            if morning:
                text = morning.content
        gpt_service = GPTService(self.user, self.db)
        data = await gpt_service.send_gpt_request(4, text)
        luck = Luck(
            User_id=self.user.id,
            text=text,
            content=data,
            create_date=now.date(),
        )
        save_db(luck, self.db)

        return {"luck": luck.content, "isCheckedToday": False}

    async def history(self) -> dict:
        now = await time_now()
        redis_key = f"history:{self.user.id}:{now.day}"
        diary_ids_json = await self.redis.get(redis_key)

        if diary_ids_json:
            diary_ids = json.loads(diary_ids_json)
            morning_diaries = [self.db.query(MorningDiary).get(diary_id) for diary_id in diary_ids["MorningDiary"]]
            night_diaries = [self.db.query(NightDiary).get(diary_id) for diary_id in diary_ids["NightDiary"]]
        else:
            n = randint(1, 2)
            count_morning = 1 if n == 1 else 2
            count_night = 2 if n == 1 else 1

            morning_diaries = self.db.query(MorningDiary).filter(
                MorningDiary.is_deleted == False,
                MorningDiary.User_id == self.user.id
            ).order_by(func.random()).limit(count_morning).all()
            night_diaries = self.db.query(NightDiary).filter(
                NightDiary.is_deleted == False,
                NightDiary.User_id == self.user.id
            ).order_by(func.random()).limit(count_night).all()

            diary_ids = {
                "MorningDiary": [diary.id for diary in morning_diaries],
                "NightDiary": [diary.id for diary in night_diaries]
            }
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            seconds_until_midnight = (midnight - now).total_seconds()
            await self.redis.set(redis_key, json.dumps(diary_ids, ensure_ascii=False), ex=int(seconds_until_midnight))

        def diary_to_dict(diary):
            diary_dict = diary.as_dict()
            diary_dict["create_date"] = diary.create_date.strftime("%Y-%m-%d %H:%M:%S") if diary.create_date else None
            diary_dict["modify_date"] = diary.modify_date.strftime("%Y-%m-%d %H:%M:%S") if diary.modify_date else None
            return diary_dict

        data = {
            "MorningDiary": [{"diary_type": 1, **diary_to_dict(diary)} for diary in morning_diaries],
            "NightDiary": [{"diary_type": 2, **diary_to_dict(diary)} for diary in night_diaries]
        }

        return data

    async def calendar(self) -> object:
        # redis에서 가져오기
        now = await time_now()
        redis_key = f"today_calendar_list:{self.user.id}:{now.day}"
        calendar_list_json = await self.redis.get(redis_key)
        if calendar_list_json:
            calendar_list = json.loads(calendar_list_json)
            return calendar_list

        upcoming_events = self.db.query(Calendar).filter(
            Calendar.User_id == self.user.id,
            Calendar.start_time >= now,
            Calendar.is_deleted == False
        ).order_by(Calendar.start_time).limit(5).all()

        await self.redis.set(redis_key, json.dumps(upcoming_events, default=diary_serializer, ensure_ascii=False), ex=1800)
        return upcoming_events

    async def weather(self, x: float, y: float) -> dict:
        async def dfs_xy_conv(code, v1, v2):
            # LCC DFS 좌표변환을 위한 기초 자료
            RE = 6371.00877  # 지구 반경(km)
            GRID = 5.0  # 격자 간격(km)
            SLAT1 = 30.0  # 투영 위도1(degree)
            SLAT2 = 60.0  # 투영 위도2(degree)
            OLON = 126.0  # 기준점 경도(degree)
            OLAT = 38.0  # 기준점 위도(degree)
            XO = 43  # 기준점 X좌표(GRID)
            YO = 136  # 기준점 Y좌표(GRID)
            DEGRAD = math.pi / 180.0
            RADDEG = 180.0 / math.pi

            re = RE / GRID
            slat1 = SLAT1 * DEGRAD
            slat2 = SLAT2 * DEGRAD
            olon = OLON * DEGRAD
            olat = OLAT * DEGRAD

            sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
            sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
            sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
            sf = math.pow(sf, sn) * math.cos(slat1) / sn
            ro = math.tan(math.pi * 0.25 + olat * 0.5)
            ro = re * sf / math.pow(ro, sn)

            rs = {}
            if code == "toXY":
                lat = v1
                lng = v2
                ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
                ra = re * sf / math.pow(ra, sn)
                theta = lng * DEGRAD - olon
                if theta > math.pi:
                    theta -= 2.0 * math.pi
                if theta < -math.pi:
                    theta += 2.0 * math.pi
                theta *= sn
                x = math.floor(ra * math.sin(theta) + XO + 0.5)
                y = math.floor(ro - ra * math.cos(theta) + YO + 0.5)
                return x, y
            else:
                # "toLL" 변환은 필요하지 않은 경우 이 부분은 구현하지 않아도 됩니다.
                pass

        async def get_api_date():
            standard_time = [2, 5, 8, 11, 14, 17, 20, 23]
            time_now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%H')
            check_time = int(time_now) - 1
            day_calibrate = 0
            # hour to api time
            while not check_time in standard_time:
                check_time -= 1
                if check_time < 2:
                    day_calibrate = 1  # yesterday
                    check_time = 23

            date_now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%Y%m%d')
            check_date = int(date_now) - day_calibrate

            return (str(check_date), (str(check_time) + '00'))

        async def select_weather_icon(sky, pty):
            if pty == '0':  # 강수 없음
                if sky == '1':  # 맑음
                    return 'sun_with_rays'
                elif sky == '3':  # 구름 많음
                    return 'sun_behind_large_cloud'
                elif sky == '4':  # 흐림
                    return 'cloud'
            elif pty in ['1', '5']:  # 비
                return 'cloud_with_rain'
            elif pty in ['2', '6']:  # 비/눈
                return 'cloud_with_snow'
            elif pty == '3':  # 눈
                return 'cloud_with_snow'
            elif pty == '4':  # 소나기
                return 'cloud_with_rain'
            elif pty == '7':  # 눈날림
                return 'cloud_with_snow'
            else:
                return 'cloud'  # 기본 아이콘

        nx, ny = await dfs_xy_conv("toXY", x, y)

        url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
        api_date, api_time = await get_api_date()
        params = {
            'serviceKey': settings.WEATHER_API_KEY,
            'pageNo': '1',
            'numOfRows': '2000',
            "ftype": "SHRT",
            'dataType': 'JSON',
            'base_date': api_date,
            'base_time': api_time,
            'nx': nx,
            'ny': ny
        }
        response = requests.get(url, params=params)
        try:
            response = response.json()
            parsed_json = response['response']['body']['items']['item']
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=4506,
            )

        target_date = parsed_json[0]['fcstDate']
        target_time = parsed_json[0]['fcstTime']
        date_calibrate = str(int(target_date) + 1) if target_time > '1300' else target_date

        passing_data = {item['category']: item['fcstValue'] for item in parsed_json if
                        item['fcstDate'] == target_date and item['fcstTime'] == target_time}
        passing_data.update({item['category']: item['fcstValue'] for item in parsed_json if
                             item['fcstDate'] == date_calibrate and item['category'] in ['TMX', 'TMN']})

        pop = passing_data.get('POP', 0)  # 강수 확률
        tmx = passing_data.get('TMX', 0)  # 최고 기온
        tmn = passing_data.get('TMN', 0)  # 최저 기온
        sky = passing_data.get('SKY')  # 하늘 상태
        pty = passing_data.get('PTY')  # 강수 형태
        weather_icon = await select_weather_icon(sky, pty)

        return {"pop": pop, "tmx": tmx, "tmn": tmn, "icon": weather_icon}