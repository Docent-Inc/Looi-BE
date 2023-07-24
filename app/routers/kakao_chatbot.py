import asyncio
from typing import Dict, Any
import aiocron
import requests
import pytz
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
from app.db.database import get_db
from app.db.models.diary_ko import Diary_ko
from app.db.models.kakao_chatbot_dream import kakao_chatbot_dream
from app.db.models.kakao_chatbot_user import kakao_chatbot_user
from app.feature.diary import createDiary
from app.feature.generate_kr import generate_text, generate_resolution_clova
from app.schemas.response.kakao_chatbot import Output, SimpleImage, SimpleText, KakaoChatbotResponse, Template
from app.schemas.request.crud import Create

'''
카카오 챗봇을 위한 API
'''

router = APIRouter(prefix="/kakao-chatbot")

# 매일 0시에 모든 user 의 day_count 를 0으로 초기화
MAX_REQUESTS_PER_DAY = 3
async def reset_day_count(db: Session = Depends(get_db)):
    users = db.query(kakao_chatbot_user).all()
    for user in users:
        user.day_count = 0
    db.commit()

# Schedule the reset_day_count function to run at 0:00 every day (KST)
cron_task = aiocron.crontab('0 0 * * *', func=reset_day_count, tz=pytz.timezone('Asia/Seoul'))

mbti_list = [
    "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ",
    "istj", "isfj", "infj", "intj", "istp", "isfp", "infp", "intp", "estp", "esfp", "enfp", "entp", "estj", "esfj", "enfj", "entj",
    "Istj", "Isfj", "Infj", "Intj", "Istp", "Isfp", "Infp", "Intp", "Estp", "Esfp", "Enfp", "Entp", "Estj", "Esfj", "Enfj", "Entj",
]

# 카카오 챗봇 callback API
async def create_callback_request_kakao(prompt: str, url: str, user_id: int, db: Session):
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
        diary_id = await createDiary(create, 2, db)


        # kakao_user_dream 생성
        kakao_user_dream = kakao_chatbot_dream(
            user_id=user_id,
            diary_id=diary_id,
        )
        db.add(kakao_user_dream)
        db.commit()

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

        user = db.query(kakao_chatbot_user).filter(kakao_chatbot_user.id == user_id).first()
        user.day_count += 1
        user.total_generated_dream += 1
        db.commit()

        # 카카오 챗봇 응답 확인
        if response.status_code == 200:
            print("kakao chatbot callback request success")
        else:
            print(f"kakao chatbot callback request fail: {response.status_code}, {response.text}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_today_luck(user_id: int, db: Session):
    '''
    오늘의 운세 생성

    :param user_day_count: 사용자의 day_count
    :param user_id: 사용자의 id
    :param db: database session을 의존성 주입합니다.
    :return:
    '''
    # kakao_chatbot_dream에서 마지막으로 생성된 꿈 가져오기
    dream = db.query(kakao_chatbot_dream).filter(kakao_chatbot_dream.user_id == user_id).order_by(kakao_chatbot_dream.id.desc()).first()
    if dream is None:
        raise HTTPException(status_code=404, detail="dream not found")
    print(dream.diary_id)
    # 오늘의 운세 생성



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

    # database에 저장된 사용자의 정보를 가져옵니다.
    user = db.query(kakao_chatbot_user).filter(kakao_chatbot_user.kakao_user_id == user_id).first()
    if user is None:
        user = kakao_chatbot_user(
            kakao_user_id=user_id,
            day_count=0,
            total_generated_dream=0,
        )
        db.add(user)
        db.commit()

    # mbti 설정하기
    if kakao_ai_request['userRequest']['utterance'].lower() in mbti_list:
        user.mbti = kakao_ai_request['userRequest']['utterance'].lower()
        db.commit()
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "mbti를 " + user.mbti + "로 설정했어요!"}}]}}

    # 도움말 보여주기
    elif kakao_ai_request['userRequest']['utterance'] == "🤔 도움말":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "도슨트AI는 mbti를 설정하면 mbti별 꿈 해몽을 해드려요!\n\nmbti를 설정하려면 mbti를 입력해주세요!\n\n꿈은 10자 이상 200자 이하로 입력해주세요"}}]}}

    # 도슨트 소개 보여주기
    elif kakao_ai_request['userRequest']['utterance'] == "🌙 도슨트":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "꿈 기록을 쉽고 재밌게, 도슨트는 개인화된 꿈 해몽을 제공하고 있습니다. 꿈을 통해 자신의 내면에 더 가까워지고, 건강한 미래를 창조할 수 있습니다."}}]}}

    # 내 정보 보여주기
    elif kakao_ai_request['userRequest']['utterance'] == "🧐 내 정보" or kakao_ai_request['userRequest']['utterance'] == "내정보":
        if user.mbti is None:
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "mbti가 아직 설정 되지 않았어요!\nmbti를 설정하려면 mbti를 입력해주세요!\n오늘 남은 요청 횟수 : " + str(MAX_REQUESTS_PER_DAY - user.day_count) + "번\n총 생성한 꿈의 수: " + str(user.total_generated_dream) + "개"}}]}}
        else:
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "내 mbti: " + user.mbti + "\n오늘 남은 요청 횟수: " + str(MAX_REQUESTS_PER_DAY - user.day_count) + "번\n총 생성한 꿈의 수: " + str(user.total_generated_dream) + "개"}}]}}

    # 곽서준 정보
    elif kakao_ai_request['userRequest']['utterance'] == "곽서준":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "도슨트의 CEO입니다. 도슨트를 만든 이유는 꿈을 통해 자신의 내면에 더 가까워지고, 건강한 미래를 창조할 수 있기 때문입니다."}}]}}

    # 조태완 정보
    elif kakao_ai_request['userRequest']['utterance'] == "조태완":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "도슨트의 CTO입니다. 도슨트를 만든 이유는 사용자들이 첨단 기술을 조금 더 손쉽게 사용할 수 있도록 하기 위해서입니다."}}]}}

    # 이예람 정보
    elif kakao_ai_request['userRequest']['utterance'] == "이예람":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "도슨트의 CMO입니다. 도슨트를 만든 이유는 사용자들이 꿈을 기록하는 것을 쉽고 재밌게 할 수 있도록 하기 위해서입니다."}}]}}

    elif kakao_ai_request['userRequest']['utterance'] == "⭐️ 오늘의 운세":
        if user.day_count == 0:
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "도슨트는 오늘 꾼 꿈을 분석해 운세를 제공해드려요!\n\n오늘 꾼 꿈을 입력해주세요!"}}]}}
        else:
            background_tasks.add_task(create_today_luck, user.id)

    # total_users 정보
    elif kakao_ai_request['userRequest']['utterance'] == "total_users":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "총 사용자 수: " + str(db.query(kakao_chatbot_user).count()) + "명"}}]}}

    # total_dreams 정보
    elif kakao_ai_request['userRequest']['utterance'] == "total_dreams":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "총 꿈의 수: " + str(db.query(kakao_chatbot_dream).count()) + "개"}}]}}

    # 무의식 분석
    elif kakao_ai_request['userRequest']['utterance'] == "👨‍⚕️ 무의식 분석":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "무의식 분석은 기능은 준비 중입니다"}}]}}

    # 꿈 해몽하기
    elif len(kakao_ai_request['userRequest']['utterance']) < 10 or len(
            kakao_ai_request['userRequest']['utterance']) > 200:
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "꿈은 10자 이상 200자 이하로 입력해주세요"}}]}}

    # 요청이 하루에 3회를 초과하면 에러 메시지를 반환합니다.
    elif user.day_count >= MAX_REQUESTS_PER_DAY:
        return {"version": "2.0",
                "template": {"outputs": [{"simpleText": {"text": "꿈 분석은 하루에 3번만 가능해요ㅠㅠ 내일 다시 시도해주세요"}}]}}

    # 백그라운드에서 create_callback_request_kakao 함수를 실행하여 카카오 챗봇에게 응답을 보냅니다.
    else:
        if user.mbti is None:
            background_tasks.add_task(create_callback_request_kakao,
                                      prompt=kakao_ai_request['userRequest']['utterance'],
                                      url=kakao_ai_request['userRequest']['callbackUrl'], user_id=user.id, db=db)
        else:
            background_tasks.add_task(create_callback_request_kakao,
                                  prompt=user.mbti + ", " + kakao_ai_request['userRequest']['utterance'],
                                  url=kakao_ai_request['userRequest']['callbackUrl'], user_id=user.id, db=db)

    # 카카오 챗봇에게 보낼 응답을 반환합니다.
    return {"version": "2.0", "useCallback": True}