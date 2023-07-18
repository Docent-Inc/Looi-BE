import asyncio
from typing import Dict, Any
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
from app.db.database import get_db
from app.feature.diary import createDiary
from app.feature.generate_kr import generate_text, generate_resolution, generate_resolution_clova
from app.schemas.response.kakao_chatbot import Output, SimpleImage, SimpleText, KakaoChatbotResponse, Template
from app.schemas.request.crud import Create

'''
카카오 챗봇을 위한 API
'''

router = APIRouter(prefix="/kakao-chatbot")

# 매일 0시에 카운터 초기화
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
user_requests = {}
MAX_REQUESTS_PER_DAY = 3
def reset_counter():
    global user_requests
    user_requests = {}

scheduler.add_job(reset_counter, 'cron', hour=0)
scheduler.start()

mbti_list = [
    "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ",
    "istj", "isfj", "infj", "intj", "istp", "isfp", "infp", "intp", "estp", "esfp", "enfp", "entp", "estj", "esfj", "enfj", "entj",
    "Istj", "Isfj", "Infj", "Intj", "Istp", "Isfp", "Infp", "Intp", "Estp", "Esfp", "Enfp", "Entp", "Estj", "Esfj", "Enfj", "Entj",
]

# 카카오 챗봇 callback API
async def create_callback_request_kakao(prompt: str, url: str, db: Session):
    '''
    카카오 챗봇 callback 함수

    :param prompt: 유저가 작성한 꿈의 내용을 담은 변수입니다.
    :param url: 카카오 챗봇에게 응답을 보낼 url입니다.
    :param db: database session을 의존성 주입합니다.
    :return: None
    '''
    try:
        if prompt[0:4] in mbti_list:
            dream_prompt = prompt[6:]
        else:
            dream_prompt = prompt
        # 꿈 생성
        task1, task2 = await asyncio.gather(
            generate_text(1, dream_prompt, 2, db),
            generate_resolution_clova(prompt, db)
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
            print("kakao chatbot callback request success")
        else:
            print("kakao chatbot callback request failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/callback", tags=["kakao"])
async def make_chatgpt_async_callback_request_to_openai_from_kakao(
        kakao_ai_request: Dict[str, Any],
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
):
    '''
    카카오 챗봇 callback API

    :param kakao_ai_request: 카카오 챗봇에서 보낸 요청을 담은 변수입니다.
    :param background_tasks: 백그라운드로 카카오 챗봇에게 응답을 보내기 위한 변수입니다.
    :param db: database session을 의존성 주입합니다.
    :return: 카카오 챗봇에게 보낼 응답을 반환합니다.
    '''
    # user_id는 카카오 챗봇 사용자의 고유 식별자입니다.
    user_id = kakao_ai_request['userRequest']['user']['id']
    # user_requests는 각 사용자의 요청 횟수를 추적하기 위해 사용됩니다.
    # user_id가 user_requests에 없으면 0으로 초기화합니다.
    if user_id not in user_requests:
        user_requests[user_id] = 0

    # 요청이 하루에 3회를 초과하면 에러 메시지를 반환합니다.
    if user_requests[user_id] >= MAX_REQUESTS_PER_DAY:
        return {"version": "2.0",
                "template": {"outputs": [{"simpleText": {"text": "꿈 분석은 하루에 3번만 가능해요ㅠㅠ 내일 다시 시도해주세요"}}]}}

    # 텍스트의 길이가 10자 이상 200자 이하인지 확인합니다. 만약 그렇지 않으면 에러 메시지를 반환합니다.
    if len(kakao_ai_request['userRequest']['utterance']) < 10 or len(
            kakao_ai_request['userRequest']['utterance']) > 200:
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "꿈은 10자 이상 200자 이하로 입력해주세요"}}]}}

    # 백그라운드에서 create_callback_request_kakao 함수를 실행하여 카카오 챗봇에게 응답을 보냅니다.
    background_tasks.add_task(create_callback_request_kakao,
                              prompt=kakao_ai_request['userRequest']['utterance'],
                              url=kakao_ai_request['userRequest']['callbackUrl'], db=db)

    # 요청 횟수를 1회 증가시킵니다.
    user_requests[user_id] += 1
    # 카카오 챗봇에게 보낼 응답을 반환합니다.
    return {"version": "2.0", "useCallback": True}