from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from collections import Counter
import numpy as np
from app.db.models import Calender
from app.feature.aiRequset import send_gpt_request, send_dalle2_request, \
    send_stable_deffusion_request, send_karlo_request, send_gpt4_request
import uuid
from io import BytesIO
import asyncio
import requests
from PIL import Image
from google.cloud import storage
from google.oauth2 import service_account
import json
from dotenv import load_dotenv
import os

from app.schemas.response import User

load_dotenv()
SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))
# async def generate_resolution_clova(text: str) -> str:
#     dream_resolution = await send_hyperclova_request(1, text)
#     return dream_resolution

async def generate_resolution_gpt(text: str) -> str:
    dream_resolution = await send_gpt4_request(2, text)
    return dream_resolution
async def generate_diary_name(message: str) -> str:
    dreamName = await send_gpt_request(2, message)
    return dreamName
async def generate_image(image_model: int, message: str):
    prompt = await send_gpt_request(3, message)

    if image_model == 1:
        dream_image_url = await send_dalle2_request(prompt)
    elif image_model == 2:
        dream_image_url = await send_stable_deffusion_request(prompt)
    elif image_model == 3:
        dream_image_url = await send_karlo_request(prompt)

    response = await asyncio.to_thread(requests.get, dream_image_url)
    img = Image.open(BytesIO(response.content))
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    # 이미지를 NumPy 배열로 변환
    img_array = np.array(img)
    img_data = img_array.reshape((-1, 3))

    # 색상 히스토그램 분석
    color_counter = Counter(map(tuple, img_data))
    dominant_color = color_counter.most_common(1)[0][0]

    # 주요 색상을 파스텔 톤으로 변환
    pastel_color = tuple(int(0.5 * c + (1 - 0.5) * 255) for c in dominant_color)

    unique_id = uuid.uuid4()
    destination_blob_name = str(unique_id) + ".png"
    bucket_name = "docent"  # 구글 클라우드 버킷 이름
    credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
    client = storage.Client(credentials=credentials, project=SERVICE_ACCOUNT_INFO['project_id'])

    with BytesIO(buffer.getvalue()) as image_file:
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(image_file)
        blob.make_public()
    return [blob.public_url, pastel_color]

async def generate_schedule(text: str, user: User, db: Session) -> str:
    retries = 2
    for i in range(retries):
        schedule = await send_gpt_request(4, text)
        try:
            schedule = json.loads(schedule)
            calender = Calender(
                User_id=user.id,
                title=schedule['title'],
                start_time=schedule['start_time'],
                end_time=schedule['end_time'],
                content=schedule['description'],
            )
            db.add(calender)
            db.commit()
            # TODO: 웹 푸시 알람

            return "일정을 저장했어요!"
        except Exception as e:
            if i < retries - 1:
                continue
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=4014
                )

