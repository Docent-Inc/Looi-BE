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
        {"role": "system", "content": "당신은 내 조각난 꿈을 완성시켜줄거야. 나 대신에 꿈을 약간의 스토리텔링을 통해 한국어로 만들어줄거고, dalle2프롬프트도 만들어줄거야, 근데 그 프롬프트 명령어는 영어로 만들어줘"},
        {"role": "system", "content": "dalle2프롬프트에 illustration라는 말을 추가해서 만들어줄거야"},  # illustration, digital image
        {"role": "system", "content": "꿈 제목은 창의적인 제목으로 너가 정해줘"},
        {"role": "system", "content": "꿈 제목(한글):, 꿈(한글):, 꿈 해몽(한글):, DALLE-2 프롬프트(영어): 이 네게의 문단으로 구성되어야 해, 각 문단의 이름이야"},
        {"role": "system", "content": "내용이 짧으면 약 250자 정도까지 되도록 추가적인 내용도 만들어줘"},
        {"role": "system", "content": "꿈 이후에 간단한 해몽 내용도 넣어줘, 해몽은 존댓말을 사용하고, 약 200자 정도로 만들어줘"},
        {"role": "system", "content": "꿈 내용은 1인칭 시점으로 작성해줘"},
    ]
    try:
        messages.append({"role": "user", "content": text})
        if messages:
            chat = openai.ChatCompletion.create(model="gpt-4", messages=messages)  # gpt-3.5-turbo
        reply = chat.choices[0].message.content

        sections = ['꿈 제목(한글)', '꿈(한글)', '꿈 해몽(한글)', 'DALLE-2 프롬프트(영어)']
        sliced_data = {}

        for i, section in enumerate(sections):
            start = reply.find(section) + len(section) + 2
            if i < len(sections) - 1:
                end = reply.find(sections[i + 1])
                sliced_data[section] = reply[start:end].strip()
            else:
                sliced_data[section] = reply[start:].strip()

        response = openai.Image.create(
            prompt=sliced_data['DALLE-2 프롬프트(영어)'],
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

        # DB에 저장
        dream = sliced_data['꿈 제목(한글)'] + " " + sliced_data['꿈(한글)']
        dream_resolution = sliced_data['꿈 해몽(한글)']

        save_to_db(text, dream, dream_resolution, picture)

    except KeyboardInterrupt:
        print("Goodbye!")
    return dream, dream_resolution, image_url