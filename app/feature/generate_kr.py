import asyncio
from app.core.current_time import get_current_time
from app.db.models.mbti_data_KR import Mbti_data_KR
from app.feature.generateImg import generate_img
from app.db.models.dream import DreamText, DreamImage
from app.db.database import get_db
from app.feature.aiRequset import send_gpt_request, send_bard_request, send_hyperclova_request

mbti_list = [
        "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ",
        "ENFJ", "ENTJ",
        "istj", "isfj", "infj", "intj", "istp", "isfp", "infp", "intp", "estp", "esfp", "enfp", "entp", "estj", "esfj",
        "enfj", "entj",
        "Istj", "Isfj", "Infj", "Intj", "Istp", "Isfp", "Infp", "Intp", "Estp", "Esfp", "Enfp", "Entp", "Estj", "Esfj",
        "Enfj", "Entj",
    ]

async def generate_text(image_model: int, text: str, userId: int, db: get_db()) -> str:
    if text[0:4] in mbti_list:
        message = text[6:]
    else:
        message = text

    async def get_dreamName(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "꿈의 내용을 이해하고 너가 재미있는 꿈의 제목을 만들어줘"},
            {"role": "user", "content": "키우는 강아지가 베란다 난간 사이에 있었는데, 겨우 구출했다. 같이 밖에 나왔는데 갑자기 사라졌다."},
            {"role": "system", "content": "수상한 강아지의 탈출 대작전"},
            {"role": "user", "content": "집 앞 공원 벤치에 앉아있는데 비둘기 두마리가 나한테 와서 구구구 거림 처음엔 무서워서 피했는데 나중에는 친해져서 쓰다듬어줌 그러다가 비둘기는 다시 자기 갈길 가고 나도 집에 감"},
            {"role": "system", "content": "비둘기와 나의 특별한 우정"},
            {"role": "user", "content": message}
        ]
        dreamName = await send_gpt_request(messages_prompt)
        # prompt = f"꿈의 내용을 이해하고 너가 재미있는 꿈의 제목을 만들어줘" \
        #          f"###꿈 내용: 기묘한 문양의 불꽃놀이를 보는데 내 키의 4배는 되어 보이는 파도가 동네 끝자락부터 덮쳐왔다. 나는 파도에 휩쓸리다가 건물 위쪽의 난간을 붙잡고 겨우 발을 디뎠다." \
        #          f"###클로바: 거대한 파도와 불꽃놀이 속의 기막힌 모험" \
        #          f"###꿈 내용: {text}"

        # # HyperClova를 호출하여 꿈 제목을 만든다.
        # dreamName = await send_hyperclova_request(prompt)
        # dreamName = dreamName.replace("###클로바:", "").lstrip()
        return dreamName

    async def DALLE2(image_model: int, message: str):
        messages_prompt = [
            {"role": "system", "content": "make just one scene a prompt for DALLE2 about this dream"},
            {"role": "system", "content": "include the word illustration, digital art and 7 world about Subject, Medium, Environment, Lighting, Color, Mood, Compoition"},
            {"role": "system", "content": "make just prompt only engilsh"},
            {"role": "system", "content": "max_length=250"},
            {"role": "user", "content": "학교 복도에서 친구랑 얘기하다가 갑자기 앞문쪽에서 좀비떼가 몰려와서 도망침. 근데 알고보니 우리반 애였음. 걔네 반 담임쌤한테 가서 말하니까 쌤이 괜찮다고 하심. 그래서 안심하고 있었는데 또다른 좀비가 와서 막 물어뜯음. 그러다가 깼는데 아직도 심장이 벌렁벌렁 거림.."},
            {"role": "system", "content": "Fleeing from a zombie horde in school, digital art, illustration, school hallway turned into a zombie apocalypse, eerie greenish light, dull and muted colors punctuated with blood red, shock and fear, focus on the chase and surprise zombie attack."},
            {"role": "user", "content": "학교 축제날이어서 여러가지 부스 체험을 했다. 나는 타로부스 가서 연애운 봤는데 상대방이랑 안 맞는다고 해서 기분 상했다. 그래도 마지막에는 좋게 끝나서 다행이라고 생각했다."},
            {"role": "system", "content": "Festival-goer getting a tarot reading, digital art, illustration, lively school festival environment, warm and inviting lighting, colorful and vibrant hues, a mix of disappointment and relief, focus on protagonist's reaction to the fortune telling."},
            {"role": "user", "content": "적에게 계속 도망치면서 세상을 구할 목표를 향해 팀원들과 향해 나아간다. 모험중에서 새로운 사람도 만나며 나아가지만 결국 나 혼자서 해내야 하는 상황에 마주친다. 하지만 목표를 향한 문제 풀이 과정에서 답도 모르지만 안풀리는 상황에 놓이고 적에게 붙잡히지는 않았지만 따라잡히게 된다."},
            {"role": "system", "content": "Hero's journey, digital art, illustration, Adventure to save world, Dramatic adventure lighting, Vivid fantasy colors, Determination and anxiety, Spotlight on the lone struggle and pursuit."},
            {"role": "user", "content": message}
        ]
        prompt = await send_gpt_request(messages_prompt)
        # prompt = f"꿈의 한 장면을 이미지로 만들건데, 한 문장으로, 250자 이내로 Subject, Medium, Environment, Lighting, Color, Mood, Composition 등에 대한 내용을 표현할 수 있는 프롬프트를 만들어줘" \
        #          f"digital art, illustration의 키워드를 포함해줘" \
        #          f"###꿈 내용: 학교 축제날이어서 여러가지 부스 체험을 했다. 나는 타로부스 가서 연애운 봤는데 상대방이랑 안 맞는다고 해서 기분 상했다. 그래도 마지막에는 좋게 끝나서 다행이라고 생각했다. " \
        #          f"###클로바: Festival-goer getting a tarot reading, digital illustration, lively school festival environment, warm and inviting lighting, colorful and vibrant hues, a mix of disappointment and relief, focus on protagonist's reaction to the fortune telling." \
        #          f"###꿈 내용: {text}"

        # # HyperClova를 호출하여 이미지 프롬프트를 생성함
        # prompt = await send_hyperclova_request(prompt)
        # prompt = prompt.replace("###클로바:", "").lstrip()

        dream_image_url = await generate_img(image_model, prompt, userId, db)
        return dream_image_url, prompt

    dream_name, L = await asyncio.gather(
        get_dreamName(message),
        DALLE2(image_model, message)
    )
    dream = message
    dream_image_url, dream_image_prompt = L

    # 데이터베이스에 DreamText 저장하기
    dream_text = DreamText(
        User_id=userId,
        User_text=text,
        dream_name=dream_name,
        dream=dream,
        DALLE2=dream_image_prompt,
        date=get_current_time(),
        is_deleted=False
    )
    db.add(dream_text)
    db.commit()
    db.refresh(dream_text)

    # 데이터베이스에 DreamImage 저장하기
    dream_image = DreamImage(
        Text_id=dream_text.id,
        dream_image_url=dream_image_url
    )
    db.add(dream_image)
    db.commit()
    db.refresh(dream_image)
    # 데이터베이스에서 id값 찾기
    dream_text_id = dream_text.id

    return dream_text_id, dream_name, dream, dream_image_url

async def generate_resolution(text: str) -> str:
    prompt = f"꿈 꿨는데 이 꿈을 짧게 해몽 해줘. 내용을 사람처럼 말해주고 첫 문장은 '이 꿈은' 으로 시작해줘. langth=150, 문단 변경없이 해몽 내용만 반환해줘. 꿈 내용 : {text}"
    dream_resolution = await send_bard_request(prompt)
    return dream_resolution

async def generate_resolution_clova(text: str, db: get_db()) -> str:
    prompt = f"꿈을 요소별로 자세하게, mbti맞춤 해몽 해줘. mbti가 입력되지 않았으면 자세하게 꿈의 요소별 일반적인 꿈 해몽 해줘." \
             f"###꿈 내용: {text}"
    # HyperClova를 호출하여 해몽 결과물을 받아옴

    dream_resolution = await send_hyperclova_request(prompt)
    dream_resolution = dream_resolution.replace("###클로바:", "").lstrip()

    # MBTI 맞춤 해몽이라면 데이터베이스에 저장함
    if text[0:4] in mbti_list:
        mbti_data = Mbti_data_KR(
            user_text=text,
            mbti_resolution=dream_resolution,
        )
        db.add(mbti_data)
        db.commit()
        db.refresh(mbti_data)

    return dream_resolution
