import openai
from app.core.openaikey import get_openai_key
from app.core.bucket import load_bucket_credentials
from io import BytesIO
import asyncio
import requests
from PIL import Image
from google.cloud import storage
from google.oauth2 import service_account
import time

openai.api_key = get_openai_key()

async def create_img(prompt: str, userId: int):
    SERVICE_ACCOUNT_INFO = load_bucket_credentials()
    print(prompt)

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

    imgName = str(userId) + str(int(time.time()))
    destination_blob_name = "testimg/" + imgName + ".png"  # 원하는 파일명을 지정하세요.
    bucket_name = "docent"  # 구글 클라우드 버킷 이름을 지정하세요.

    client = create_storage_client_hardcoded()
    with BytesIO(dream_image_data) as image_file:
        bucket_image_url = await upload_image_to_gcp(client, bucket_name, image_file, destination_blob_name)

    return bucket_image_url
