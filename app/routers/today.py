import json
from datetime import datetime
from random import randint

import aioredis
import requests
from app.core.config import settings
import pytz
from urllib.parse import urlencode, unquote
import redis as redis
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.apiDetail import ApiDetail
from app.core.security import get_current_user, time_now
from app.db.database import get_db, get_redis_client
from app.db.models import Calender, MorningDiary, NightDiary, Report, Luck
from app.feature.generate import generate_luck
from app.schemas.response import User, ApiResponse
import pytz
import math

async def dfs_xy_conv(code, v1, v2):
    # LCC DFS 좌표변환을 위한 기초 자료
    RE = 6371.00877 # 지구 반경(km)
    GRID = 5.0 # 격자 간격(km)
    SLAT1 = 30.0 # 투영 위도1(degree)
    SLAT2 = 60.0 # 투영 위도2(degree)
    OLON = 126.0 # 기준점 경도(degree)
    OLAT = 38.0 # 기준점 위도(degree)
    XO = 43 # 기준점 X좌표(GRID)
    YO = 136 # 기준점 Y좌표(GRID)
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

async def get_api_date() :
    standard_time = [2, 5, 8, 11, 14, 17, 20, 23]
    time_now = datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%H')
    check_time = int(time_now) - 1
    day_calibrate = 0
	#hour to api time
    while not check_time in standard_time :
        check_time -= 1
        if check_time < 2 :
            day_calibrate = 1 # yesterday
            check_time = 23

    date_now = datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%Y%m%d')
    check_date = int(date_now) - day_calibrate

    return (str(check_date), (str(check_time) + '00'))

router = APIRouter(prefix="/today")

@router.get("/calender", tags=["Today"])
async def get_calender(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    today = await time_now()
    upcoming_events = db.query(Calender).filter(
        Calender.User_id == current_user.id,
        Calender.start_time >= today,
        Calender.is_deleted == False
    ).order_by(Calender.start_time).limit(5).all()
    return ApiResponse(
        data=upcoming_events
    )
get_calender.__doc__ = f"[API detail]({ApiDetail.get_calender})"

def default_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

@router.get("/history", tags=["Today"])
async def get_record(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        redis: aioredis.Redis = Depends(get_redis_client),
) -> ApiResponse:
    now = await time_now()
    today_str = now.strftime('%Y-%m-%d')
    redis_key = f"history:{today_str}:user_{current_user.id}"

    cached_data_json = await redis.get(redis_key)

    if cached_data_json:
        cached_data = json.loads(cached_data_json)
        return ApiResponse(data=cached_data)

    n = randint(1, 2)
    if n == 1:
        count_morning = 1
        count_night = 2
    else:
        count_morning = 2
        count_night = 1

    random_morning_diaries = db.query(MorningDiary).filter(
        MorningDiary.is_deleted == False,
        MorningDiary.User_id == current_user.id
    ).order_by(func.random()).limit(count_morning).all()
    random_night_diaries = db.query(NightDiary).filter(
        NightDiary.is_deleted == False,
        NightDiary.User_id == current_user.id
    ).order_by(func.random()).limit(count_night).all()

    data = {
        "MorningDiary": [diary.as_dict() for diary in random_morning_diaries],
        "NightDiary": [diary.as_dict() for diary in random_night_diaries]
    }

    ttl = (now.replace(hour=23, minute=59, second=59) - now).seconds
    data_json = json.dumps(data, default=default_converter)
    await redis.setex(redis_key, ttl, data_json)

    return ApiResponse(data=data)
get_record.__doc__ = f"[API detail]({ApiDetail.get_record})"

@router.get("/luck", tags=["Today"])
async def luck(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
    now = await time_now()
    cached_luck = db.query(Luck).filter(
        Luck.User_id == current_user.id,
        Luck.create_date == now.date(),
        Luck.is_deleted == False
    ).first()

    if cached_luck:
        return ApiResponse(data={"luck": cached_luck.content, "isCheckedToday": True})

    luck_content = await generate_luck(current_user, db)
    return ApiResponse(data={"luck": luck_content,  "isCheckedToday": False})
luck.__doc__ = f"[API detail]({ApiDetail.generate_luck})"

@router.get("/weather", tags=["Today"])
async def get_weather(
    x: float,
    y: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse:
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

    target_date = parsed_json[0]['fcstDate']  # get date and time
    target_time = parsed_json[0]['fcstTime']

    date_calibrate = target_date  # date of TMX, TMN
    if target_time > '1300':
        date_calibrate = str(int(target_date) + 1)

    passing_data = {}
    for one_parsed in parsed_json:
        if one_parsed['fcstDate'] == target_date and one_parsed['fcstTime'] == target_time:  # get today's data
            passing_data[one_parsed['category']] = one_parsed['fcstValue']

        if one_parsed['fcstDate'] == date_calibrate and (
                one_parsed['category'] == 'TMX' or one_parsed['category'] == 'TMN'):
            passing_data[one_parsed['category']] = one_parsed['fcstValue']
    try:
        pop = passing_data['POP']
    except KeyError:
        pop = 0
    try:
        tmx = passing_data['TMX']
    except KeyError:
        tmx = 0
    try:
        tmn = passing_data['TMN']
    except KeyError:
        tmn = 0
    print(passing_data)

    return ApiResponse(data={"pop": pop, "tmx": tmx, "tmn": tmn})
