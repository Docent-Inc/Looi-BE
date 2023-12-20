import json
from datetime import datetime, timedelta
from random import randint
from typing import Annotated

import aioredis
import requests

from app.core.config import settings
import pytz
from urllib.parse import urlencode, unquote
import redis as redis
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.security import get_current_user, time_now
from app.db.database import get_db, get_redis_client
from app.db.models import Calendar, MorningDiary, NightDiary, Report, Luck, User
from app.schemas.response import ApiResponse
import pytz
import math

from app.service.today import TodayService


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

@router.get("/calendar", tags=["Today"])
async def get_today_calendar(
    today_service: Annotated[TodayService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await today_service.calendar()
    )
@router.get("/history", tags=["Today"])
async def get_today_history(
    today_service: Annotated[TodayService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data=await today_service.history()
    )

@router.get("/luck", tags=["Today"])
async def get_today_luck(
    today_service: Annotated[TodayService, Depends()],
) -> ApiResponse:
    return ApiResponse(
        data={"luck": await today_service.luck()}
    )

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
    sky = passing_data.get('SKY')
    pty = passing_data.get('PTY')
    weather_icon = await select_weather_icon(sky, pty)

    return ApiResponse(data={"pop": pop, "tmx": tmx, "tmn": tmn, "icon": weather_icon})
