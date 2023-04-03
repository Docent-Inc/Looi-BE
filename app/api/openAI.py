import openai
import requests
from PIL import Image
from io import BytesIO

openai.api_key = "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"

messages = [
    {"role": "system", "content": "당신은 내 조각난 꿈을 완성시켜줄거야. 나 대신에 꿈일기를 약간의 스토리텔링을 통해 한국어로 만들어줄거고, dalle2프롬프트도 만들어줄거야, 근데 그 프롬프트 명령어는 영어로 만들어줘"},
    {"role": "system", "content": "dalle2그림을 illustration로 만들어줄거야"},
    {"role": "system", "content": "꿈 일기 이름은 너가 정해줘"},
    {"role": "system", "content": "DALLE-2 프롬프트 (영어): 이후에 프롬프트 작성해줘"},
]
def generate_text(text: str) -> str:
    try:
        text = input("You: ")
        messages.append({"role": "user", "content": text})
        if messages:
            chat = openai.ChatCompletion.create(model="gpt-4", messages=messages)  # gpt-3.5-turbo
        reply = chat.choices[0].message.content
        print(reply)
        prompt = reply[reply.find('DALLE-2 프롬프트 (영어):') + 19:]
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
        img.save("generated_image.jpg")


    except KeyboardInterrupt:
        print("Goodbye!")

    return f"GPT 결과: {reply}"

