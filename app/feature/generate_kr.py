import asyncio
from app.core.current_time import get_current_time
from app.feature.generateImg import generate_img
from app.db.models.dream import DreamText, DreamImage
from app.db.database import get_db
from app.feature.aiRequset import send_gpt_request, send_bard_request, send_hyperclova_request


async def generate_text(image_model: int, text: str, userId: int, db: get_db()) -> str:
    async def get_dreamName(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "꿈의 내용을 이해하고 너가 재미있는 꿈의 제목을 만들어줘"},
            {"role": "user", "content": message}
        ]
        dreamName = await send_gpt_request(messages_prompt)
        return dreamName

    async def DALLE2(image_model: int, message: str):
        messages_prompt = [
            {"role": "system", "content": "make just one scene a prompt for DALLE2 about this dream"},
            {"role": "system", "content": "include the word illustration and 7 world about Subject, Medium, Environment, Lighting, Color, Mood, Compoition"},
            {"role": "system", "content": "make just prompt only engilsh"},
            {"role": "system", "content": "max_length=100"},
            {"role": "user", "content": message}
        ]
        prompt = await send_gpt_request(messages_prompt)

        dream_image_url = await generate_img(image_model, prompt, userId, db)
        return dream_image_url, prompt

    dream_name, L = await asyncio.gather(
        get_dreamName(text),
        DALLE2(image_model, text)
    )
    dream = text
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

async def generate_resolution_mvp(text: str) -> str:
    prompt = f"꿈 꿨는데 이 꿈을 짧게 해몽 해줘. 내용을 사람처럼 말해주고 첫 문장은 '이 꿈은' 으로 시작해줘. langth=150, 문단 변경없이 해몽 내용만 반환해줘. 꿈 내용 : {text}"
    dream_resolution = await send_bard_request(prompt)
    return dream_resolution

async def generate_resolution_clova(text: str) -> str:
    prompt = f"꿈을 mbti맞춤 해몽 해줘." \
             f"\n\n꿈 내용: entj, 실수로 친구를 죽였는데 다른 친구가 냉장고에 숨기고 청소부를 고용해 아무도 모르게 숨기자고 했다. 시체청소부는 정해진 약속 시간에 오고 자기의 얼굴을 보는 사람은 죽인다고 해 친구와 함께 나가려는 찰나, 도착한 청소부와 마주쳤다. 그래서 옥상으로 도망쳤는데 옥상엔 노을진 금빛 바다가 펼쳐져있고 뒤에는 청소부가 기다리고 있어서 앞으로도 뒤로도 갈 수 없었다.\n" \
             f"\n해몽: 이 꿈은 일상의 부담감이나 책임에 대한 두려움을 반영하고 있을 수 있습니다. 실수로 친구를 죽이게 되는 상황은 실수로 큰 문제를 일으키거나, 중요한 것을 잃어버리는 두려움을 보여주고 있습니다. 이는 당신이 완벽을 추구하는 경향이 있으며, 실수에 대한 과도한 걱정을 가지고 있음을 나타냅니다. 다른 친구와의 협력, 또는 그의 방법을 통해 문제를 해결하려는 시도는 당신이 효과적인 해결책을 찾아내거나 구상하려는 노력을 보여줍니다. 하지만 청소부와 마주치는 상황은 계획이 완전히 이루어지지 않아 예기치 못한 결과를 초래할 수 있음을 보여주는 것일 수 있습니다. 옥상에서의 금빛 바다는 아름다움과 평온함을 상징할 수 있지만, 청소부를 피해 갈 곳이 없는 상황은 당신이 더 이상 문제를 피하거나 회피할 수 없음을 보여주는 상징적인 요소일 수 있습니다. 이 꿈은 현재 당신이 직면하고 있는 어려움이나 도전, 그리고 이를 해결하기 위한 당신의 노력을 반영하고 있습니다. 어려움에 직면했을 때의 두려움보다는 당신이 상황을 직시하고, 필요한 조치를 취해야 함을 상기시키고 있습니다." \
             f"\n\n꿈 내용: {text}"
    dream_resolution = await send_hyperclova_request(prompt)
    return dream_resolution
