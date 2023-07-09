from io import BytesIO
import asyncio
import requests
from PIL import Image
from aiohttp import ClientSession
from fastapi import HTTPException
from google.cloud import storage
from google.oauth2 import service_account
import openai
from dotenv import load_dotenv
import os
import pytz
from datetime import datetime
import json
from sqlalchemy.orm import Session
from starlette import status

from app.db.models import User
from app.db.models.dream import DreamText, DreamImage

load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")
stable_diffusion_api_key = os.getenv("STABLE_DIFFUSION")
SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))

async def generate_img(prompt: str, userId: int, db: Session):
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

    async def get_Stable_Diffusion_url(prompt):
        url = "https://stablediffusionapi.com/api/v3/text2img"

        data = {
            "key": stable_diffusion_api_key,
            "prompt": prompt,
            "negative_prompt": None,
            "width": "512",
            "height": "512",
            "samples": "1",
            "num_inference_steps": "20",
            "safety_checker": "yes",
            "enhance_prompt": "yes",
            "seed": None,
            "guidance_scale": 7.5,
            "webhook": None,
            "track_id": None
        }

        headers = {"Content-Type": "application/json"}

        async with ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Stable Diffusion API request failed"
                    )
                result = await response.json()
                return result["output"][0]
    async def download_image(url):
        response = await asyncio.to_thread(requests.get, url)
        img = Image.open(BytesIO(response.content))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    user = db.query(User).filter(User.id == userId).first()
    if user.subscription_status == True:
        dream_image_url = await get_Stable_Diffusion_url(prompt)
    else:
        dream_image_url = await get_image_url(prompt)
    dream_image_data = await download_image(dream_image_url)

    korea_timezone = pytz.timezone("Asia/Seoul")
    korea_time = datetime.now(korea_timezone)
    formatted_time = korea_time.strftime("%Y%m%d%H%M%S")
    imgName = str(userId) + str(formatted_time)
    # TODO: 디렉토리 이름을 dreams/userid/imageName.png로 바꿔야함
    destination_blob_name = "mvp/dreams/" + str(userId) + "/" + imgName + ".png"
    # destination_blob_name = "testimg/" + imgName + ".png"
    bucket_name = "docent"  # 구글 클라우드 버킷 이름을 지정하세요.

    client = create_storage_client_hardcoded()
    with BytesIO(dream_image_data) as image_file:
        bucket_image_url = await upload_image_to_gcp(client, bucket_name, image_file, destination_blob_name)
    return bucket_image_url
async def get_text_data(textId: int, user_id: int, db: Session):
    # 데이터베이스에서 textId와 user_id를 사용하여 데이터를 검색하는 코드를 작성하세요.
    text_data = db.query(DreamText).filter(DreamText.id == textId, DreamText.User_id == user_id).first()
    # 쿼리를 실행한 후, 해당하는 데이터가 없으면 None을 반환하고, 데이터가 있으면 해당 데이터를 반환하세요.
    return text_data
async def get_image_count(imageId: int, db: Session):
    # 데이터베이스에서 imageId와 user_id를 사용하여 데이터의 갯수를 검색합니다.
    image_count = db.query(DreamImage).filter(DreamImage.Text_id == imageId).count()
    # 쿼리를 실행한 후, 해당하는 데이터가 없으면 0을 반환하고, 데이터가 있으면 해당 데이터의 갯수를 반환합니다.
    return image_count
async def additional_generate_image(textId, user_id, db):
    # 생성된 이미지의 갯수가 3개가 넘는지 확인합니다.
    if await get_image_count(textId, db) >= 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미지 생성 횟수 초과")
    # 데이터베이스에서 textId와 user_id를 확인 후 prompt 가져오기
    text_data = await get_text_data(textId, user_id, db)
    if text_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="생성된 꿈이 없습니다.")
    prompt = text_data.DALLE2  # 생성된 DALLE2 프롬프트 정보 불러오기
    # 새로운 꿈 이미지 생성
    dream_image_url = await generate_img(prompt, user_id, db)
    # 데이터베이스에 dream_image_url 저장
    dream_image = DreamImage(
        Text_id=textId,
        dream_image_url=dream_image_url
    )
    db.add(dream_image)
    db.commit()
    db.refresh(dream_image)
    return dream_image_url
