import openai
import asyncio
from app.gptapi.generateImg import generate_img
from app.db.models.dream import DreamText, DreamImage
from app.db.database import get_db
from app.gptapi.gptRequset import send_gpt_request

async def generate_text(text: str, userId: int, db: get_db()) -> str:
    '''
    async def get_gpt_response(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "당신은 내 조각난 꿈을 완성시켜줄거야. 나 대신에 꿈을 약간의 스토리텔링을 통해 한국어로 만들어줄거야"},
            {"role": "system",
             "content": "꿈 제목은 창의적인 제목으로 너가 정해주고, 꿈 내용은 1인칭 시점으로 작성해줘, 만약 내용이 짧으면 추가적인 내용을 만들어줘"},
            {"role": "system", "content": "꿈 내용은 120자가 넘지 않도록 만들어줘"},
            {"role": "system", "content": "꿈 제목은 []로 감싸주고 이어서 내용을 만들어줘"}, {"role": "user", "content": message}]
        response = await send_gpt_request(messages_prompt)
        return response

    async def DALLE2(message: str):
        try:
            messages_prompt = [
                {"role": "system", "content": message},
                {"role": "system", "content": "이 꿈을 바탕으로 DALLE2에 넣을 프롬프트를 영어로 만들어줘, illustration라는 단어를 포함시켜줘"}
            ]
            chat = openai.ChatCompletion.create(model="gpt-4", messages=messages_prompt)
        except Exception as e:
            print(e)
            return "OpenAI API Error"
        dream_image_url = await generate_img(chat.choices[0].message.content, userId)
        return dream_image_url, chat.choices[0].message.content

    dream, L = await asyncio.gather(
        get_gpt_response(text),
        DALLE2(text)
    )
    dream_name = dream[dream.find("[") + 1:dream.find("]")]
    dream = dream[dream.find("]") + 1:]
    dream_image_url, dream_image_prompt = L
    '''

    dream = "test"
    dream_name = "test"
    dream_image_url = "test"
    dream_image_prompt = "test"

    # 데이터베이스에 DreamText 저장하기
    dream_text = DreamText(
        User_id=userId,
        User_text=text,
        dream_name=dream_name,
        dream=dream,
        DALLE2=dream_image_prompt
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

    return dream_name, dream, dream_image_url