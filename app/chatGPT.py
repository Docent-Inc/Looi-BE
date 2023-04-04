import openai
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime

from app.db.dream import save_to_db, create_table, convertToBinaryData

# gptkey.txt 파일 읽어오기
with open("app/gptkey.txt", "r") as f:
    openai.api_key = f.read().rstrip()

def generate_text(text: str):
    messages = [
        {"role": "system", "content": "당신은 내 조각난 꿈을 완성시켜줄거야. 나 대신에 꿈일기를 약간의 스토리텔링을 통해 한국어로 만들어줄거고, dalle2프롬프트도 만들어줄거야, 근데 그 프롬프트 명령어는 영어로 만들어줘"},
        {"role": "system", "content": "dalle2그림을 illustration로 만들어줄거야"},
        {"role": "system", "content": "꿈 일기 이름은 너가 정해줘"},
        {"role": "system", "content": "DALLE-2 프롬프트 (영어): 이후에 프롬프트 작성해줘"},
        {"role": "system", "content": "내용이 짧으면 약간의 추가적인 내용도 만들어줘"},
        {"role": "system", "content": "맨 마지막 부분에 간단한 꿈 해몽 내용도 넣어줘"},
        {"role": "system", "content": "꿈 일기 이름, 꿈 해몽, DALLE-2 프롬프트 (영어). 이 세게의 문단으로 구성되어야 해"},
    ]
    try:
        messages.append({"role": "user", "content": text})
        if messages:
            chat = openai.ChatCompletion.create(model="gpt-4", messages=messages)  # gpt-3.5-turbo
        reply = chat.choices[0].message.content
        dream_start = reply.find("꿈 일기 이름: ") + len("꿈 일기 이름: ")
        dream_end = reply.find("꿈 해몽: ")
        dream = reply[dream_start:dream_end].rstrip()

        dream_resolution_start = reply.find("꿈 해몽: ") + len("꿈 해몽: ")
        dream_resolution_end = reply.find("DALLE-2 프롬프트 (영어)")
        dream_resolution = reply[dream_resolution_start:dream_resolution_end].rstrip()

        prompt_start = reply.find('DALLE-2 프롬프트 (영어):') + len('DALLE-2 프롬프트 (영어):')
        prompt = reply[prompt_start:]

        response = openai.Image.create(
            prompt=prompt,
            n=1,  # 생성할 이미지 수
            size="512x512",  # 이미지 크기
            response_format="url"  # 응답 형식
        )

        # 이미지 URL 추출
        image_url = response['data'][0]['url']

        # 이미지 다운로드 및 저장
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        picture = buffer.getvalue()

        save_to_db(text, dream, dream_resolution, picture)

    except KeyboardInterrupt:
        print("Goodbye!")
    return dream, dream_resolution, image_url