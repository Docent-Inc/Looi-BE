from io import BytesIO
import asyncio
import requests
from PIL import Image
from google.cloud import storage
from google.oauth2 import service_account
import time
import openai
from dotenv import load_dotenv
import os
import pytz
from datetime import datetime
import json
load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")
SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))

async def generate_img(prompt: str, userId: int):
    async def upload_image_to_gcp(client, bucket_name, image_file, destination_blob_name):
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(image_file)
        blob.make_public()
        return blob.public_url

    def create_storage_client_hardcoded():
        credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
        return storage.Client(credentials=credentials, project=SERVICE_ACCOUNT_INFO['project_id'])

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

    dream_image_url = await get_image_url(prompt)
    dream_image_data = await download_image(dream_image_url)

    korea_timezone = pytz.timezone("Asia/Seoul")
    korea_time = datetime.now(korea_timezone)
    formatted_time = korea_time.strftime("%Y%m%d%H%M%S")
    imgName = str(userId) + str(formatted_time)
    # TODO: 디렉토리 이름을 dreams/userid/imageName.png로 바꿔야함
    destination_blob_name = "dreams/" + str(userId) + "/" + imgName + ".png"
    destination_blob_name = "testimg/" + imgName + ".png"
    bucket_name = "docent"  # 구글 클라우드 버킷 이름을 지정하세요.

    client = create_storage_client_hardcoded()
    with BytesIO(dream_image_data) as image_file:
        bucket_image_url = await upload_image_to_gcp(client, bucket_name, image_file, destination_blob_name)
    return bucket_image_url
