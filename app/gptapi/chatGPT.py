import openai
import requests
from PIL import Image
from io import BytesIO
import asyncio
import time
from app.schemas.survey import SurveyData
from google.cloud import storage
from google.oauth2 import service_account

from app.db.dream import save_to_db

# gptkey.txt 파일 읽어오기
with open("app/gptapi/gptkey.txt", "r") as f:
    openai.api_key = f.read().rstrip()

async def generate_text(text: str, survay_data: SurveyData) -> str:
    if text.find("성한빈") != -1 or text.find("한빈") != -1 or text.find("장하오") != -1:
        return "그만해", "너 IP다 털렸다.", "수고해", "경찰서에서 보자", "https://www.police.go.kr/index.do"


    start_time = time.time()  # 실행 시작 시간 기록
    L = []
    SERVICE_ACCOUNT_INFO = {
        "type": "service_account",
        "project_id": "bold-landing-380312",
        "private_key_id": "07d19af2d593c76000c947f9efc2f808a5dd526c",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDEiszeXaRxfJ7p\nNxgjqt2Lv08j/35u1ihwyMXIx8XUgcY+LgSMHzFRViq7JFc2C1cApHn1e4DV8GKY\nttyP5k8Tx/5v50EFCUG8soqQRLEOTW/0QMmoPRKiegPICg7BFvQ7KZP9tl1ptLUN\nEJG7AdIXnz49XM1FibJSefhzdfJK0IWS6t5pCihLhuf7e8y8QYkwh5i9AAedbSdO\ndb3D3XGBmLtvJdnDDbXcBRIw/rm4zSUInEW/hHfbZe+EV4miig/uHFjCd9GUkeQg\n/61wd8Gr0f8HNrEelQ3tDdZPRhVxYM7jyNrbezV02nDNPHLgIiihsHgz7xgv8Rid\n4zsHOKyBAgMBAAECggEACBEya4Yoc8gLtcLfKMegpFXL58xa4i3EJyz2gVFB24Eg\nI/k7kozNN2t0AY5yTfOVNJ+LqfnRxfZB9ca7suRfJo608N7rGkvQ+O/TJCzNn6qq\nB7qJDHDFTQn5EcLn7CEHEU6ZlnZfyzDxpYGimaxvdSzCHz6p5krKmPwMqKCUu2FV\nPfvnwzob/EDrGLH7SaFefsEIICmzzVKRlMiCCIHVYSihsUXl1JuulxxPvhwYKkaY\nRgPNQnXmhsjYl8DL7Tw/aHyJvKF/Oxu8RSO0Krip1es2tuuCHc1zuPP/bCgX1JVS\nGQOEodhbLnr8JNvlQK/v2oGA34crJaK9em7uMPoECQKBgQD07reDNT4qKfwpwQ6O\nVac4NJW05+XBy3Ep0pVEVHLk0+hANnY6eWCyv3zlhmsQUFM2oYepXFpM1ym4CxS0\nfBzf7N53DD5RCZIbioJ8U9XErDv2IJBjpp9RDxF3cH/YelDNyhHjbZsWLpWze06o\ngz1DMiF8fBpznnLncgpDgsPZHwKBgQDNbFLJG6L0lGsE4Q6mK4ldWByhrDJy1P6R\noDjm+Kj9c9Ocurk5aSCfHEF6qdS64jfVOHD+AQgxzas9spwhR+inRlaamxRmaNZZ\nih6pXOMHmgmyqqxLcMStOJyYt5yOXSmieOsm4hNqL8sOatvjbntmQAk8tt//qXxf\ngFEy6R+mXwKBgQCXQ549//HGZGuA9eOhb7B3+7HBKb4xMw1OQOlCa80RGPXEQl49\nupxHiA8ASUVxq8nYYWXA6HI0JmVzbhR5anUCreyuJPePYJPFQoNXeQb6EUxusqm5\ngTu++clVtDqgXNnuXa8yf4xZ5Kc7Uxm+5F4/U4Ruts43PVHFMh64lteRDQKBgClV\niZbj07dJAfu6WVtAWWSJ7UDuyDvo9cxRpAF9uWs+Wi8oN0sBB0pcwiQvdhmgmUFz\nGPFTPdXfn3xLqzTbJko6UgTL/Z/Zqn/b1e2YPipyaU8lHoQTjc+ZG5FzKLJQtqb1\nk8OALA3qzf35rIMn4PajHfi0h4AHF3qT9EK9O9wbAoGBAIAkcV4BkToqy5ISnAEW\nsr6jxi37GrT5mxSf9Xy/OjhVp1hqOROueRHAbFZkJrXUOD3G3dG53CsgvoUfZRGY\n+x0HG0M/2ZBkUmA556WLh8K4n4L/AKhYkHD/+qPp9DDnVwIpaDdihJh2M9wH8ehe\nCl2Guw8GfrtqdpPTfqVraOmM\n-----END PRIVATE KEY-----\n",
        "client_email": "test-555@bold-landing-380312.iam.gserviceaccount.com",
        "client_id": "113573215612941765368",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-555%40bold-landing-380312.iam.gserviceaccount.com"
    }
    async def upload_image_to_gcs(client, bucket_name, image_data, destination_blob_name):
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        with BytesIO(image_data) as image_file:
            blob.upload_from_file(image_file)

    async def get_time(name, start_time):
        print(f"{name} took {time.time() - start_time} seconds")

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

    async def get_gpt_response(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": "당신은 내 조각난 꿈을 완성시켜줄거야. 나 대신에 꿈을 약간의 스토리텔링을 통해 한국어로 만들어줄거야"},
            {"role": "system",
             "content": "꿈 제목은 창의적인 제목으로 너가 정해주고, 꿈 내용은 1인칭 시점으로 작성해줘, 만약 내용이 짧으면 추가적인 내용을 만들어줘"},
            {"role": "system", "content": "꿈 내용은 120자가 넘지 않도록 만들어줘"},
            {"role": "system", "content": "꿈 제목은 []로 감싸주고 이어서 내용을 만들어줘"}, {"role": "user", "content": message}]
        response = await send_gpt_request(messages_prompt)
        await get_time("get_gpt_response", start_time)
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

    async def download_image(url):
        response = await asyncio.to_thread(requests.get, url)
        img = Image.open(BytesIO(response.content))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    async def get_dream_resolution(message: str) -> str:
        messages_prompt = [
            {"role": "system", "content": message},
            {"role": "system", "content": "꿈 내용을 바탕으로 꿈 해몽을 만들어줘"},
            {"role": "system", "content": "꿈 해몽은 70자가 넘지 않도록 해줘"},
        ]
        response = await send_gpt_request(messages_prompt)
        await get_time("get_dream_resolution", start_time)
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
        await get_time("get_today_luck", start_time)
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
        # dream_image_data = await download_image(dream_image_url)
        dream_image_data = " "
        await get_time("DALLE2", start_time)
        return [dream_image_data, dream_image_url]

    results, L = await asyncio.gather(
        get_gpt_response_and_more(text),
        DALLE2(text)
    )
    dream_name, dream, dream_resolution, today_luck = results
    dream_image_data, dream_image_url = L
    destination_blob_name = dream_name + ".png"  # 원하는 파일명을 지정하세요.
    bucket_name = "bmongsmongimg"  # 구글 클라우드 버킷 이름을 지정하세요.

    def create_storage_client_hardcoded():
        credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
        return storage.Client(credentials=credentials, project=SERVICE_ACCOUNT_INFO['project_id'])

    # client = create_storage_client_hardcoded()
    # await upload_image_to_gcs(client, bucket_name, dream_image_data, destination_blob_name)

    save_to_db(text, dream_name + dream, dream_resolution + today_luck, survay_data)

    await get_time("total", start_time)

    return dream_name, dream, dream_resolution, today_luck, L[1]

