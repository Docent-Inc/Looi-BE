import openai
import asyncio
from app.core.openaikey import get_openai_key
from app.gptapi.generateImg import create_img
from app.db.models.dream import DreamText, DreamImage
from app.db.database import get_db
openai.api_key = get_openai_key()

async def generate_text(text: str, userId: int, db: get_db()) -> str:
    async def send_gpt_request(messages_prompt, retries=3):
        for i in range(retries):
            try:
                chat = openai.ChatCompletion.create(model="gpt-4", messages=messages_prompt)
                return chat.choices[0].message.content
            except Exception as e:
                print(e)
                if i < retries - 1:
                    print(f"Retrying {i + 1} of {retries}...")
                else:
                    print("Failed to get response after maximum retries")
                    return "ERROR"
    async def get_gpt_response(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "당신은 내 조각난 꿈을 완성시켜줄거야. 나 대신에 꿈을 약간의 스토리텔링을 통해 한국어로 만들어줄거야"},
            {"role": "system",
             "content": "꿈 제목은 창의적인 제목으로 너가 정해주고, 꿈 내용은 1인칭 시점으로 작성해줘, 만약 내용이 짧으면 추가적인 내용을 만들어줘"},
            {"role": "system", "content": "꿈 내용은 120자가 넘지 않도록 만들어줘"},
            {"role": "system", "content": "꿈 제목은 []로 감싸주고 이어서 내용을 만들어줘"}, {"role": "user", "content": message}]
        response = await send_gpt_request(messages_prompt)
        return response

    async def get_dream_resolution(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": message},
            {"role": "system", "content": "꿈 내용을 바탕으로 꿈 해몽을 만들어줘"},
            {"role": "system", "content": "꿈 해몽은 70자가 넘지 않도록 해줘"},
        ]
        response = await send_gpt_request(messages_prompt)
        return response

    async def get_today_luck(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": message},
            {"role": "system", "content": "꿈을 바탕으로 오늘의 운세를 만들어줘"},
            {"role": "system", "content": "오늘의 운세는 30자가 넘지 않도록 해줘"},
            {"role": "system", "content": "제목없이 내용만 만들어줘, 현실을 반영해서 조심해야될 것 또는 좋은 일이 일어날 것 또는 꿈을 바탕으로 해야될 일을 적어줘"},
            {"role": "system", "content": "오늘은 으로 시작해줘"},
        ]
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
        dream_image_url = await create_img(chat.choices[0].message.content, userId)
        return dream_image_url, chat.choices[0].message.content

    async def get_gpt_response_and_more(message: str):
        dream = await get_gpt_response(message)
        if dream == "ERROR":
            return "ERROR"
        dream_name = dream[dream.find("[") + 1:dream.find("]")]
        dream = dream[dream.find("]") + 1:]
        dream_resolution, today_luck = await asyncio.gather(
            get_dream_resolution(dream),
            get_today_luck(dream)
        )
        return dream_name, dream, dream_resolution, today_luck

    results, L = await asyncio.gather(
        get_gpt_response_and_more(text),
        DALLE2(text)
    )
    dream_name, dream, dream_resolution, today_luck = results
    dream_image_url, dream_image_prompt = L

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

    return dream_name, dream, dream_resolution, today_luck, dream_image_url