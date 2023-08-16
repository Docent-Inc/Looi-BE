import asyncio
from typing import Dict, Any
import aiocron
import requests
import pytz
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
from app.db.database import get_db, get_SessionLocal
from app.db.models.diary import Diary
from app.db.models.diary_ko import Diary_ko
from app.db.models.dream_score import dream_score
from app.db.models.kakao_chatbot_dream import kakao_chatbot_dream
from app.db.models.kakao_chatbot_user import kakao_chatbot_user, kakao_chatbot_diary, kakao_chatbot_memo, \
    kakao_chatbot_total_chat
from app.db.models.today_luck import today_luck
from app.feature.aiRequset import send_hyperclova_request
from app.feature.diary import createDiary
from app.feature.generate_kr import generate_text, generate_resolution_clova
from app.schemas.response.kakao_chatbot import Output, SimpleImage, SimpleText, KakaoChatbotResponse, Template
from app.schemas.request.crud import Create

'''
카카오 챗봇을 위한 API
'''

router = APIRouter(prefix="/kakao-chatbot")

# 매일 0시에 모든 user 의 count 를 0으로 초기화
MAX_REQUESTS_PER_DAY = 10
async def reset_day_count():
    SessionLocal = get_SessionLocal()
    db = SessionLocal()
    try:
        users = db.query(kakao_chatbot_user).all()
        for user in users:
            user.day_count = 0
            user.diary_count = 0
            user.luck_count = 0
        db.commit()
        print("Reset kakao day_count successfully")
    finally:
        db.close()


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
            dream_name=dream_name,
            is_deleted=False,
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

        # 카카오 챗봇 응답 확인
        if response.status_code == 200:
            print("kakao chatbot callback request success")
        else:
            print(f"kakao chatbot callback request fail: {response.status_code}, {response.text}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        # 심리 점수 부여
        prompt = f"꿈의 내용을 통해 100점 만점으로 심리상태 점수를 부여해줘" \
                 f"###꿈 내용: entj, 엄마를 인천공항에 데려다주고 쌀국수도 먹었어" \
                 f"###클로바: 87" \
                 f"###꿈 내용: 치즈 김밥과 참치 김밥을 손에 들고 폭우가 쏟아지는 도시를 행복한 표정으로 뛰어간다." \
                 f"###클로바: 95" \
                 f"###꿈 내용: isfp, 내가 좋아하는 연예인이랑 같이 데이트하다가 집 가는 길에 차 타고 가다가 교통사고 나서 둘 다 죽음" \
                 f"###클로바: 34" \
                 f"###꿈 내용: {prompt}"

        status_score = await send_hyperclova_request(prompt)
        status_score = status_score.replace("###클로바:", "").lstrip()

        user = db.query(kakao_chatbot_user).filter(kakao_chatbot_user.id == user_id).first()
        user.day_count += 1
        user.total_generated_dream += 1
        if user.status_score == 0:
            user.status_score = int(status_score)
        user.status_score = int(user.status_score * 2 / 3 + int(status_score) / 3)
        db.add(user)

        score = dream_score(
            diary_id=diary_id,
            score=int(status_score),
        )
        db.add(score)
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_today_luck(url: str, user_id: int, db: Session):
    '''
    오늘의 운세 생성

    :param user_day_count: 사용자의 day_count
    :param user_id: 사용자의 id
    :param db: database session을 의존성 주입합니다.
    :return:
    '''
    # kakao_chatbot_dream에서 마지막으로 생성된 꿈 가져오기
    dream = db.query(kakao_chatbot_dream).filter(kakao_chatbot_dream.user_id == user_id).order_by(kakao_chatbot_dream.id.desc()).first()
    if dream is not None:
        dream_text = db.query(Diary_ko).filter(Diary_ko.Diary_id == dream.diary_id).first()
    if dream_text is not None:
        text = dream_text.dream
    else:
        text = ""

    # 오늘의 운세 생성
    prompt = f"꿈의 내용을 보고 오늘의 운세를 만들어줘, 꿈의 내용은 참고만 하고 내용에 녹아들어가게 해주고, 사자성어로 운세 총운을 만들어줘, 꿈의 내용이 없다면 그냥 오늘의 운세를 만들어줘" \
             f"###꿈 내용: 나랑 친한 친구들이 다같이 모여서 놀다가 갑자기 한명씩 사라져서 마지막엔 나만 남았다. 그래서 혼자 울다가 깼다." \
             f"###클로바: 오늘의 운세 총운은 “여어득수” 입니다. 기대치 않았던 곳에서 큰 지원을 받게 되니 일을 더욱 잘 풀리고 몸과 마음 또한 더없이 기쁘고 편할 수 있을 것입니다. 당신에게 스트레스로 작용했던 일이 있다면 당신의 노력이 바탕이 되어 해결할 수 있는 기회도 잡을 수 있습니다. 또한 주변사람들로부터 도움이나 조언을 통해서 자신의 방향을 잡을 수도 있습니다. 그러나 자신의 의지를 잃지 않는 것도 중요한 부분입니다. 당신에게 닥친 이 기회를 잘 활용한다면 충분히 많은 성과와 발전이 있을 것이지요. 조금 더 분발하세요." \
             f"###꿈 내용: 제가 좋아하는 연예인이랑 사귀는 꿈 꿨어요! 완전 행복했어요ᄒᄒ" \
             f"###클로바: 오늘의 운세 총운은 “이럴수가” 입니다. 마음이 다소 들떠 있는 날이니 추스르되 긴장은 푸시기 바랍니다. 너무 무리하는 것은 오히려 당신에게 이로울 수 없는 것입니다. 또한 당신이 원하는 만큼의 목표에 가까워왔다고 하여 마음을 놓아버리거나 쉽게 생각하는 태도로 좋지 않습니다. 끝까지 마무리할 수 있도록 최선을 노력을 다하는 것이 좋고 마음을 좀 더 여유롭게 가지고 행동하는 것이 필요하겠습니다. 또한 그저 평소에 해왔던 것과 같이 행동하면 어려울 것이 없는 날이니 눈앞에 놓인 것에 충실해 보시기 바랍니다." \
             f"###꿈 내용: {text}"
    # HyperClova를 호출하여 오늘의 운세를 받아옴

    luck = await send_hyperclova_request(prompt)
    luck = luck.replace("###클로바:", "").lstrip()

    # 카카오 챗봇 응답
    outputs = [
        Output(simpleText=SimpleText(text=f"{luck}"))
    ]
    request_body = KakaoChatbotResponse(
        version="2.0",
        template=Template(outputs=outputs)
    ).dict()
    response = requests.post(url, json=request_body)

    luck = today_luck(
        user_text=text,
        today_luck=luck,
    )
    db.add(luck)
    db.commit()
    db.refresh(luck)

    user = db.query(kakao_chatbot_user).filter(kakao_chatbot_user.id == user_id).first()
    user.luck_count += 1
    db.commit()
    db.refresh(user)

    # 카카오 챗봇 응답 확인
    if response.status_code == 200:
        print("kakao chatbot callback request success")
    else:
        print(f"kakao chatbot callback request fail: {response.status_code}, {response.text}")

async def create_diary(prompt: str, url: str, user_id: int, db: Session):
    '''
    카카오 챗봇에서 보낸 요청을 받아 일기를 생성합니다.

    :param url:
    :param user_id:
    :param db:
    :return:
    '''
    try:
        # 일기 생성
        id, dream_name, dream, dream_image_url = await generate_text(1, prompt, 2, db)

        # 다이어리 생성
        create = Create(
            dream_name=dream_name,
            dream=dream,
            image_url=dream_image_url,
            resolution="일기",
            checklist="checklist",
            is_public=True,
        )
        diary_id = await createDiary(create, 2, db)

        # kakao_user_diary 생성
        kakao_user_diary = kakao_chatbot_diary(
            user_id=user_id,
            diary_id=diary_id,
            dream_name=dream_name,
            is_deleted=False,
        )
        db.add(kakao_user_diary)
        db.commit()

        # 다이어리 가져오기
        diary = db.query(Diary).filter(Diary.id == diary_id).first()
        # diary.create_date = 20230508104128
        date = diary.create_date[0:4] + "년 " + diary.create_date[4:6] + "월 " + diary.create_date[6:8] + "일"

        outputs = [
            Output(simpleImage=SimpleImage(imageUrl=dream_image_url)),
            Output(simpleText=SimpleText(text=f"{dream_name}\n\n{date}\n일기 내용: {dream}"))
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
            print(f"kakao chatbot callback request fail: {response.status_code}, {response.text}")

        user = db.query(kakao_chatbot_user).filter(kakao_chatbot_user.id == user_id).first()
        user.diary_count += 1
        db.commit()
        db.refresh(user)


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/callback", tags=["kakao"])
async def kakao_ai_chatbot_callback(
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
    total_chat = db.query(kakao_chatbot_total_chat).first()
    total_chat.count += 1
    db.commit()
    db.refresh(total_chat)

    # user_id는 카카오 챗봇 사용자의 고유 식별자입니다.
    user_id = kakao_ai_request['userRequest']['user']['id']

    # uset_text는 카카오 챗봇 사용자가 입력한 텍스트입니다.
    user_text = kakao_ai_request['userRequest']['utterance']

    # database에 저장된 사용자의 정보를 가져옵니다.
    user = db.query(kakao_chatbot_user).filter(kakao_chatbot_user.kakao_user_id == user_id).first()
    if user is None:
        user = kakao_chatbot_user(
            kakao_user_id=user_id,
            day_count=0,
            total_generated_dream=0,
            status_score=0,
            only_luck_count=0,
            luck_count=0,
            mode=0,
        )
        db.add(user)
        db.commit()

    if user_text == "안녕":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "안녕하세요! 저는 도슨트AI에요!"}}]}}

    # mbti 설정하기
    elif user_text.lower() in mbti_list:
        user.mbti = kakao_ai_request['userRequest']['utterance'].lower()
        db.commit()
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "mbti를 " + user.mbti + "로 설정했어요!"}}]}}

    # 오늘의 운세 보기
    elif user_text == "⭐️ 오늘의 운세":
        if user.luck_count != 0:
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "오늘의 운세는 이미 생성되었어요. 내일 다시 시도해주세요!"}}]}}
        else:
            background_tasks.add_task(create_today_luck, url=kakao_ai_request['userRequest']['callbackUrl'], user_id=user.id, db=db)
            return {"version": "2.0", "useCallback": True, "data": {"text": "오늘의 운세를 분석중이에요!"}}

    # 🌙 꿈 기록장 mode
    elif user_text == "🌙 꿈 기록장":
        user.mode = 1
        db.commit()
        my_dreams = db.query(kakao_chatbot_dream).filter(kakao_chatbot_dream.user_id == user.id, kakao_chatbot_dream.is_deleted == 0).all()
        if len(my_dreams) == 0:
            return {"version": "2.0",
                    "template": {"outputs": [{"simpleText": {"text": "🌙 꿈 기록장에 오신 것을 환영해요!\n\n꿈을 기록하려면 꿈을 입력해주세요!"}}]}}
        else:
            text = ""
            number = 1
            for dream_name in my_dreams:
                text += f"\n{number}. {dream_name.dream_name}"
                number += 1
            return {"version": "2.0",
                    "template": {"outputs": [{"simpleText": {"text": "🌙 꿈 기록장에 오신 것을 환영해요!\n꿈을 기록하려면 꿈을 입력해주세요!\n꿈 번호를 입력하시면 다시 볼 수 있어요!\n" + text + "\n\n삭제하시려면 '삭제 번호'를 입력해주세요! 예시: 삭제 1"}}]}}

    # 📔 일기장 mode
    elif user_text == "📔 일기장":
        user.mode = 2
        db.commit()
        my_diarys = db.query(kakao_chatbot_diary).filter(kakao_chatbot_diary.user_id == user.id, kakao_chatbot_diary.is_deleted == 0).all()
        if len(my_diarys) == 0:
            return {"version": "2.0",
                    "template": {"outputs": [{"simpleText": {"text": "📔 일기장에 오신 것을 환영해요!\n\n오늘 하루를 기록해보세요!"}}]}}
        else:
            text = ""
            number = 1
            for dream_name in my_diarys:
                text += f"\n{number}. {dream_name.dream_name}"
                number += 1
            return {"version": "2.0",
                    "template": {"outputs": [
                        {"simpleText": {"text": "📔 일기장에 오신 것을 환영해요!\n오늘 하루를 기록해보세요!\n\n일기 번호를 입력하시면 다시 볼 수 있어요!\n" + text + "\n\n삭제하시려면 '삭제 번호'를 입력해주세요! 예시: 삭제 1"}}]}}

    # 📝 메모장 mode
    elif user_text == "📝 메모장":
        user.mode = 3
        db.commit()
        my_memos = db.query(kakao_chatbot_memo).filter(kakao_chatbot_memo.user_id == user.id, kakao_chatbot_memo.is_deleted == 0).all()
        if len(my_memos) == 0:
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "📝 메모장에 오신 것을 환영합니다!\n\n메모를 입력해주세요!"}}]}}
        else:
            text = ""
            number = 1
            for memeo in my_memos:
                text += f"\n{number}. {memeo.text}"
                number += 1
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "📝 메모장에 오신 것을 환영합니다!\n\n" + text + "\n\n삭제하시려면 '삭제 번호'를 입력해주세요! 예시: 삭제 1"}}]}}

    # 기록 보기
    elif len(user_text) <= 3 or user_text.split(" ")[0] == "삭제":
        try:
            if user_text.split(" ")[0] == "삭제":
                dream_number = int(user_text.split(" ")[1])
                if user.mode == 1: # 꿈 기록장
                    my_dreams = db.query(kakao_chatbot_dream).filter(kakao_chatbot_dream.user_id == user.id, kakao_chatbot_dream.is_deleted == 0).all()
                    if dream_number > len(my_dreams):
                        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "꿈 번호를 잘못 입력하셨어요!"}}]}}
                    else:
                        # is_deleted를 1로 바꿔서 삭제
                        my_dreams[dream_number - 1].is_deleted = 1
                        db.commit()
                        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "꿈을 삭제했어요!"}}]}}
                elif user.mode == 2: # 일기장
                    my_diarys = db.query(kakao_chatbot_diary).filter(kakao_chatbot_diary.user_id == user.id, kakao_chatbot_diary.is_deleted == 0).all()
                    if dream_number > len(my_diarys):
                        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "일기 번호를 잘못 입력하셨어요!"}}]}}
                    else:
                        # is_deleted를 1로 바꿔서 삭제
                        my_diarys[dream_number - 1].is_deleted = 1
                        db.commit()
                        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "일기를 삭제했어요!"}}]}}
                elif user.mode == 3: # 메모장
                    my_memos = db.query(kakao_chatbot_memo).filter(kakao_chatbot_memo.user_id == user.id, kakao_chatbot_memo.is_deleted == 0).all()
                    if dream_number > len(my_memos):
                        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "메모 번호를 잘못 입력하셨어요!"}}]}}
                    else:
                        # is_deleted를 1로 바꿔서 삭제
                        my_memos[dream_number - 1].is_deleted = 1
                        db.commit()
                        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "메모를 삭제했어요!"}}]}}
            else:
                dream_number = int(user_text)
                if user.mode == 1: # 꿈 기록장
                    my_dreams = db.query(kakao_chatbot_dream).filter(kakao_chatbot_dream.user_id == user.id, kakao_chatbot_dream.is_deleted == 0).all()
                    if dream_number > len(my_dreams):
                        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "꿈 번호를 잘못 입력하셨어요!"}}]}}
                    else:
                        diary_id = my_dreams[dream_number - 1].diary_id
                        my_dream_url = db.query(Diary).filter(Diary.id == diary_id).first()
                        my_dream = db.query(Diary_ko).filter(Diary_ko.Diary_id == diary_id).first()
                        return {"version": "2.0", "template": {
                            "outputs": [{"simpleImage": {"imageUrl": my_dream_url.image_url}}, {"simpleText": {
                                "text": my_dream.dream_name + "\n\n꿈 내용: " + my_dream.dream + "\n\n해몽: " + my_dream.resolution}}]}}
                elif user.mode == 2: # 일기장
                    my_diarys = db.query(kakao_chatbot_diary).filter(kakao_chatbot_diary.user_id == user.id, kakao_chatbot_diary.is_deleted == 0).all()
                    if dream_number > len(my_diarys):
                        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "일기 번호를 잘못 입력하셨어요!"}}]}}
                    else:
                        diary_id = my_diarys[dream_number - 1].diary_id
                        my_dream_url = db.query(Diary).filter(Diary.id == diary_id).first()
                        my_dream = db.query(Diary_ko).filter(Diary_ko.Diary_id == diary_id).first()
                        date = my_dream_url.create_date[0:4] + "년 " + my_dream_url.create_date[4:6] + "월 " + my_dream_url.create_date[6:8] + "일"
                        return {"version": "2.0", "template": {
                            "outputs": [{"simpleImage": {"imageUrl": my_dream_url.image_url}}, {"simpleText": {
                                "text": my_dream.dream_name + "\n\n" + date + "\n일기 내용: " + my_dream.dream}}]}}

        except:
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "잘못된 입력입니다!"}}]}}

    # 내 정보 보여주기
    elif user_text == "🧐 내 정보":
        my_dreams = db.query(kakao_chatbot_dream).filter(kakao_chatbot_dream.user_id == user.id, kakao_chatbot_dream.is_deleted == 0).all()
        my_diarys = db.query(kakao_chatbot_diary).filter(kakao_chatbot_diary.user_id == user.id, kakao_chatbot_diary.is_deleted == 0).all()
        my_memos = db.query(kakao_chatbot_memo).filter(kakao_chatbot_memo.user_id == user.id, kakao_chatbot_memo.is_deleted == 0).all()
        if my_dreams is None:
            my_dreams = []
        if my_diarys is None:
            my_diarys = []
        if my_memos is None:
            my_memos = []
        if user.mbti == None:
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "👨‍🏫 MBTI를 설정해주세요! MBTI를 입력해주시면 더 정확한 해몽이 가능해요\n\n" +"무의식 점수: " + str(user.status_score) + "점\n\n" + "꿈 기록장: " + str(len(my_dreams)) + "개\n\n" + "일기장: " + str(len(my_diarys)) + "개\n\n" + "메모장: " + str(len(my_memos)) + "개"}}]}}
        else:
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "👨‍🏫 MBTI: " + user.mbti + "\n\n" +"무의식 점수: " + str(user.status_score) + "점\n\n" + "꿈 기록장: " + str(len(my_dreams)) + "개\n\n" + "일기장: " + str(len(my_diarys)) + "개\n\n" + "메모장: " + str(len(my_memos)) + "개"}}]}}

    # 도움말 보여주기
    elif user_text == "🤔 도움말":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "📃설명서\n\n☝️기본 기능\n\n👉 기록 하기\n여러분이 기록하실 주제를 메뉴에서 클릭하시고 채팅으로 입력해주세요.\nex) 일기장 클릭 -> 일기 입력\n\n👉 목록 보기\n메뉴에서 보고싶은 기록을 선택하세요.\nex) 꿈일기장 클릭\n\n✌️ 특별한 기능\n\n✡️ MBTI를 설정해주세요. 채팅으로 여러분의 mbti를 입력해주시면 설정되고 더 정확한 해몽이 가능해요\n\n🔮오늘의 운세 메뉴를 클릭하시면 꿈 내용을 기반으로 오늘의 운세를 알려드립니다\n\n또한 메뉴에서 다양한 기능을 활용해 보세요🙏"}}]}}

    # 도슨트 소개 보여주기
    elif user_text == "🌙 도슨트":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "꿈 기록을 쉽고 재밌게, 도슨트는 개인화된 꿈 해몽을 제공하고 있습니다. 꿈을 통해 자신의 내면에 더 가까워지고, 건강한 미래를 창조할 수 있습니다."}}]}}

    # 곽서준 정보
    elif user_text == "곽서준":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "👨‍💼 도슨트의 CEO입니다. 도슨트를 만든 이유는 꿈을 통해 자신의 내면에 더 가까워지고, 건강한 미래를 창조할 수 있기 때문입니다."}}]}}

    # 조태완 정보
    elif user_text == "조태완":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "👨‍💻 도슨트의 CTO입니다. 도슨트를 만든 이유는 사용자들이 첨단 기술을 조금 더 손쉽게 사용할 수 있도록 하기 위해서입니다."}}]}}

    # 이예람 정보
    elif user_text == "이예람":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "👩‍💼 도슨트의 CMO입니다. 도슨트를 만든 이유는 사용자들이 꿈을 기록하는 것을 쉽고 재밌게 할 수 있도록 하기 위해서입니다."}}]}}

    # total_users 정보
    elif user_text == "total_users":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "총 사용자 수: " + str(db.query(kakao_chatbot_user).count()) + "명"}}]}}

    # total_dreams 정보
    elif user_text == "total_dreams":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "총 꿈의 수: " + str(db.query(kakao_chatbot_dream).count()) + "개"}}]}}

    # total_diary 정보
    elif user_text == "total_diary":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "총 일기의 수: " + str(db.query(kakao_chatbot_diary).count()) + "개"}}]}}

    # total_memo 정보
    elif user_text == "total_memo":
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "총 메모의 수: " + str(db.query(kakao_chatbot_memo).count()) + "개"}}]}}

    # total_chat 정보
    elif user_text == "total_chat":
        total_chat = db.query(kakao_chatbot_total_chat).first()
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "총 채팅의 수: " + str(total_chat.count) + "개"}}]}}

    # 무의식 분석
    elif user_text == "👨‍⚕️ 무의식 분석":
        user.only_luck_count += 1
        db.commit()
        return {"version": "2.0", "template": {"outputs": [{"textCard": {"text": "안녕하세요! 🌼 저희 서비스를 더 좋게 만들기 위해 여러분의 소중한 의견을 듣고 싶어요. 함께 성장하는 서비스를 위해 손길 한 번, 부탁드려요!\n\n추첨을 통해 스타벅스 기프티콘을 선물해드려요💛", "buttons": [{"action": "webLink", "label": "커피 받으러가기", "webLinkUrl": "https://walla.my/survey/nt6dhKP3LIJsX0QUwGwi"}]}}]}}

    elif user.mode == 0:
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "😉 하단 메뉴 중 하나를 설정해주세요!"}}]}}

    elif user_text >= 500:
        return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "😦 글자가 너무 길어요. 500자 이내로 입력해주세요!"}}]}}

    # 백그라운드에서 create_callback_request_kakao 함수를 실행하여 카카오 챗봇에게 응답을 보냅니다.
    else:
        if user.mode == 1:
            if user.day_count > MAX_REQUESTS_PER_DAY:
                return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "하루 요청량이 초과되었어요. 내일 다시 이용해주세요!"}}]}}
            elif user.mbti is None:
                background_tasks.add_task(create_callback_request_kakao,
                                          prompt=user_text,
                                          url=kakao_ai_request['userRequest']['callbackUrl'], user_id=user.id, db=db)
            else:
                background_tasks.add_task(create_callback_request_kakao,
                                      prompt=user.mbti + ", " + user_text,
                                      url=kakao_ai_request['userRequest']['callbackUrl'], user_id=user.id, db=db)

            return {"version": "2.0", "useCallback": True, "data": {"text": "🌙 꿈을 분석하는 중이에요!\n20초 정도 소요될 거 같아요"}}

        elif user.mode == 2:
            if user.diary_count > MAX_REQUESTS_PER_DAY:
                return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "하루 요청량이 초과되었어요. 내일 다시 이용해주세요!"}}]}}
            background_tasks.add_task(create_diary, prompt=user_text, url=kakao_ai_request['userRequest']['callbackUrl'], user_id=user.id, db=db)
            return {"version": "2.0", "useCallback": True, "data": {"text": "📔 일기를 저장 하는 중이에요!\n20초 정도 소요될 거 같아요"}}

        elif user.mode == 3:
            memo = kakao_chatbot_memo(
                user_id=user.id,
                text=user_text,
                is_deleted=False,
            )
            db.add(memo)
            db.commit()
            db.refresh(memo)
            return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "📝 메모를 저장했어요!\n\n메뉴를 눌러 메모를 확인하세요!"}}]}}

    return {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "잘못된 입력입니다!"}}]}}