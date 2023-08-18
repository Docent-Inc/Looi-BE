import uuid
from io import BytesIO
import asyncio
import requests
from PIL import Image
from fastapi import HTTPException
from google.cloud import storage
from google.oauth2 import service_account
import openai
from dotenv import load_dotenv
import os
import json
from starlette import status
from app.feature.aiRequset import send_stable_deffusion_request, send_karlo_request
load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")
SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))


async def upload_image_to_gcp(client, bucket_name, image_file, destination_blob_name):
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(image_file)
    blob.make_public()
    return blob.public_url


async def create_storage_client_hardcoded():
    credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
    return storage.Client(credentials=credentials, project=SERVICE_ACCOUNT_INFO['project_id'])


async def get_image_url(prompt):
    try:
        response = await asyncio.to_thread(
            openai.Image.create,
            prompt=prompt,
            n=1,
            size="512x512",
            response_format="url"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return response['data'][0]['url']

async def download_image(url):
    response = await asyncio.to_thread(requests.get, url)
    img = Image.open(BytesIO(response.content))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

async def generate_image_model(image_model: int, prompt: str):




    if image_model == 1:
        dream_image_url = await get_image_url(prompt)
    elif image_model == 2:
        dream_image_url = await send_stable_deffusion_request(prompt)
    elif image_model == 3:
        dream_image_url = await send_karlo_request(prompt)

    dream_image_data = await download_image(dream_image_url)
    unique_id = uuid.uuid4()
    destination_blob_name = str(unique_id) + ".png"
    bucket_name = "docent"  # 구글 클라우드 버킷 이름
    client = await create_storage_client_hardcoded()
    with BytesIO(dream_image_data) as image_file:
        bucket_image_url = await upload_image_to_gcp(client, bucket_name, image_file, destination_blob_name)
    return bucket_image_url
