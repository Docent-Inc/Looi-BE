from typing import Tuple
import openai
import asyncio
import time
import os
from dotenv import load_dotenv
from app.schemas.survey import SurveyData
from app.models.dream import Dream
from app.db.database import SessionLocal
load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")

async def save_to_db_async(text, dream, dream_resolution, survey_data) -> Tuple[str, str, str, str, str]:
    def save_to_db(text, dream, dream_resolution, survey_data: SurveyData):
        session = SessionLocal()
        new_dream = Dream(
            dreamTime=survey_data.dreamTime,
            isRecordDream=survey_data.isRecordDream,
            isShare=survey_data.isShare,
            isRecordPlatform=survey_data.isRecordPlatform,
            sex=survey_data.sex,
            mbti=survey_data.mbti,
            department=survey_data.department,
            text=text,
            dream_name=dream,
            dream_resolution=dream_resolution
        )  # image_url=image_url)
        session.add(new_dream)
        session.commit()
        session.close()
    save_to_db(text, dream, dream_resolution, survey_data)

async def generate_text(text: str, survey_data: SurveyData) -> str:
    start_time = time.time()  # 실행 시작 시간 기록

    async def get_time(name, start_time):
        print(f"{name} took {time.time() - start_time} seconds")

    async def send_gpt_request(messages_prompt, retries=2):
        for i in range(retries):
            try:
                chat = await asyncio.to_thread(
                    openai.ChatCompletion.create,
                    model="gpt-4",
                    messages=messages_prompt
                )
                return chat.choices[0].message.content
            except Exception as e:
                print(e)
                if i < retries - 1:
                    print(f"Retrying {i + 1} of {retries}...")
                else:
                    print("Failed to get response after maximum retries")
                    return "ERROR"
                await asyncio.sleep(1)

    async def get_gpt_response_and_more(message: str):
        dream = await get_gpt_response(message)
        if dream == "ERROR":
            return "ERROR"
        dream_name = dream[dream.find("[") + 1:dream.find("]")]
        dream = dream[dream.find("]") + 1:]
        dream_image_url = asyncio.create_task(DALLE2(dream))
        today_luck_task = asyncio.create_task(get_today_luck(dream))
        dream_resolution_task = asyncio.create_task(get_dream_resolution(dream))
        dream_resolution, today_luck, dream_image_url = await asyncio.gather(dream_resolution_task, today_luck_task, dream_image_url)
        return dream_name, dream, dream_resolution, today_luck, dream_image_url

    async def get_gpt_response(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "당신은 내 조각난 꿈을 완성시켜줄거야. 나 대신에 꿈을 약간의 스토리텔링을 통해 한국어로 만들어줄거야"},
            {"role": "system",
             "content": "꿈 제목은 창의적인 제목으로 너가 정해주고, 꿈 내용은 1인칭 시점으로 작성해줘, 만약 내용이 짧으면 추가적인 내용을 만들어줘"},
            {"role": "system", "content": "꿈 내용은 110자가 넘지 않도록 만들어줘"},
            {"role": "system", "content": "꿈 제목은 []로 감싸주고 이어서 내용을 만들어줘"}, {"role": "user", "content": message}]
        response = await send_gpt_request(messages_prompt)
        asyncio.create_task(get_time("Dream text", start_time))
        return response

    async def get_image_url(prompt):
        response = await asyncio.to_thread(
            openai.Image.create,
            prompt=prompt,
            n=1,
            size="512x512",
            response_format="url"
        )
        return response['data'][0]['url']

    async def get_dream_resolution(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": message},
            {"role": "system", "content": "꿈 내용을 바탕으로 꿈 해몽을 만들어줘"},
            {"role": "system", "content": "꿈 해몽은 60자가 넘지 않도록 해줘"},
        ]
        response = await send_gpt_request(messages_prompt)
        asyncio.create_task(get_time("Resolution dream", start_time))
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
        asyncio.create_task(get_time("Today luck", start_time))
        return response
    async def DALLE2(message: str) -> str:
        try:
            messages_prompt = [
                {"role": "system", "content": message},
                {"role": "system", "content": "꿈을 바탕으로 DALLE2에 넣을 프롬프트를 영어로 만들어줘, illustration라는 단어를 포함시켜줘"}
            ]
            chat = openai.ChatCompletion.create(model="gpt-4", messages=messages_prompt)
        except Exception as e:
            print(e)
            return "OpenAI API Error"
        dream_image_url = await get_image_url(chat.choices[0].message.content)
        asyncio.create_task(get_time("DALLE2 image", start_time))
        return dream_image_url

    dream_name, dream, dream_resolution, today_luck, dream_image_url = await get_gpt_response_and_more(text)

    asyncio.create_task(save_to_db_async(text, dream_name + dream, dream_resolution + today_luck, survey_data))

    asyncio.create_task(get_time("Total", start_time))
    return dream_name, dream, dream_resolution, today_luck, dream_image_url