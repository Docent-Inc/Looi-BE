import asyncio
import logging
from typing import Dict, Any

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
from app.db.database import get_db
from app.feature.diary import createDiary
from app.feature.generate_kr import generate_text, generate_resolution
from app.schemas.kakao_chatbot import Output, SimpleImage, SimpleText, KakaoChatbotResponse, Template, \
    KakaoChatbotResponseCallback, KakaoAIChatbotRequest
from app.schemas.request.crud import Create

'''
카카오 챗봇을 위한 API
'''

router = APIRouter(prefix="/kakao-chatbot")

# # 매일 0시에 카운터 초기화
# scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
user_requests = {}
MAX_REQUESTS_PER_DAY = 3
# def reset_counter():
#     global user_requests
#     user_requests = {}
#
# scheduler.add_job(reset_counter, 'cron', hour=0)
# scheduler.start()

# 카카오 챗봇 callback API
async def create_callback_request_kakao(prompt: str, url: str, db: Session) -> dict:
    try:

        # 꿈 생성
        task1, task2 = await asyncio.gather(
            generate_text(prompt, 2, db),
            generate_resolution(prompt)
        )
        id, dream_name, dream, dream_image_url = task1
        dream_resolution = task2

        # 다이어리 생성
        create = Create(
            dream_name=dream_name,
            dream=dream,
            image_url=dream_image_url,
            resolution=dream_resolution,
            checklist="checklist",
            is_public=True,
        )
        await createDiary(create, 2, db)

        # 카카오 챗봇 응답
        outputs = [
            Output(simpleImage=SimpleImage(imageUrl=dream_image_url)),
            Output(simpleText=SimpleText(text=f"{dream_name}\n\n꿈 내용: {dream}\n\n해몽: {dream_resolution}"))
        ]
        request_body = KakaoChatbotResponse(
            version="2.0",
            template=Template(outputs=outputs)
        ).dict()
        response = requests.post(url, json=request_body)

        # 카카오 챗봇 응답 확인
        if response.status_code == 200:
            print("success")
        else:
            logging.error(response.status_code)

    except Exception as e:
        logging.error(e)

@router.post("/callback", tags=["kakao"], response_model=KakaoChatbotResponseCallback)
async def make_chatgpt_async_callback_request_to_openai_from_kakao(
        kakao_ai_request: KakaoAIChatbotRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
):
    # Userid로 카운트를 해서 한국시간 기준 12시에 초기화
    # 총 3회까지 가능함
    print(kakao_ai_request)

    user_id = kakao_ai_request.userRequest.user.id
    # user_requests에 user_id가 없으면 0으로 초기화
    if user_id not in user_requests:
        user_requests[user_id] = 0

    # 3회 이상 요청했으면 에러 메시지 출력
    if user_requests[user_id] >= MAX_REQUESTS_PER_DAY:
        return KakaoChatbotResponseCallback(version="2.0", template=Template(
            outputs=[Output(simpleText=SimpleText(text="꿈 분석은 하루에 3번만 가능해요ㅠㅠ 내일 다시 시도해주세요"))]))

    # 텍스트의 길이가 10자 이상 200자 이하인지 확인
    kakao_ai_request.userRequest.utterance = kakao_ai_request.userRequest.utterance[3:] # "꿈에서 " 제거
    if len(kakao_ai_request.userRequest.utterance) < 10 or len(kakao_ai_request.userRequest.utterance) > 200:
        return KakaoChatbotResponseCallback(version="2.0", template=Template(
            outputs=[Output(simpleText=SimpleText(text="꿈은 10자 이상 200자 이하로 입력해주세요"))]))

    # 백그라운드로 카카오 챗봇에게 응답을 보냄
    background_tasks.add_task(create_callback_request_kakao,
                              prompt=kakao_ai_request.userRequest.utterance, url=kakao_ai_request.userRequest.callbackUrl, db=db)

    user_requests[user_id] += 1
    return KakaoChatbotResponseCallback(version="2.0", useCallback=True)