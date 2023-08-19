from app.db.database import get_db
from app.feature.aiRequset import send_gpt_request, send_hyperclova_request, send_dalle2_request, \
    send_stable_deffusion_request, send_karlo_request
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
load_dotenv()
SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))

async def generate_resolution_clova(text: str) -> str:
    prompt = f"꿈을 요소별로 자세하게, mbti맞춤 해몽 해줘. mbti가 입력되지 않았으면 자세하게 꿈의 요소별 일반적인 꿈 해몽 해줘." \
             f"###꿈 내용: {text}"
    # HyperClova를 호출하여 해몽 결과물을 받아옴
    dream_resolution = await send_hyperclova_request(prompt)
    dream_resolution = dream_resolution.replace("###클로바:", "").lstrip()
    return dream_resolution


async def generate_diary_name(message: str) -> str:
    messages_prompt = [
        {"role": "system", "content": "이야기의 내용을 이해해서, 너가 재미있는 제목을 만들어줘"},
        {"role": "user", "content": "키우는 강아지가 베란다 난간 사이에 있었는데, 겨우 구출했다. 같이 밖에 나왔는데 갑자기 사라졌다."},
        {"role": "system", "content": "수상한 강아지의 탈출 대작전"},
        {"role": "user", "content": "집 앞 공원 벤치에 앉아있는데 비둘기 두마리가 나한테 와서 구구구 거림 처음엔 무서워서 피했는데 나중에는 친해져서 쓰다듬어줌 그러다가 비둘기는 다시 자기 갈길 가고 나도 집에 감"},
        {"role": "system", "content": "비둘기와 나의 특별한 우정"},
        {"role": "user", "content": message}
    ]
    dreamName = await send_gpt_request(messages_prompt)
    return dreamName

async def generate_image(image_model: int, message: str):
    messages_prompt = [
        {"role": "system", "content": "make just one scene a prompt for generate image model about this text"},
        {"role": "system", "content": "include the word illustration, digital art and 7 world about Subject, Medium, Environment, Lighting, Color, Mood, Compoition"},
        {"role": "system", "content": "make just prompt only engilsh"},
        {"role": "system", "content": "max_length=250"},
        {"role": "user", "content": "학교 복도에서 친구랑 얘기하다가 갑자기 앞문쪽에서 좀비떼가 몰려와서 도망침. 근데 알고보니 우리반 애였음. 걔네 반 담임쌤한테 가서 말하니까 쌤이 괜찮다고 하심. 그래서 안심하고 있었는데 또다른 좀비가 와서 막 물어뜯음. 그러다가 깼는데 아직도 심장이 벌렁벌렁 거림.."},
        {"role": "system", "content": "Fleeing from a zombie horde in school, digital art, illustration, school hallway turned into a zombie apocalypse, eerie greenish light, dull and muted colors punctuated with blood red, shock and fear, focus on the chase and surprise zombie attack."},
        {"role": "user", "content": "학교 축제날이어서 여러가지 부스 체험을 했다. 나는 타로부스 가서 연애운 봤는데 상대방이랑 안 맞는다고 해서 기분 상했다. 그래도 마지막에는 좋게 끝나서 다행이라고 생각했다."},
        {"role": "system", "content": "Festival-goer getting a tarot reading, digital art, illustration, lively school festival environment, warm and inviting lighting, colorful and vibrant hues, a mix of disappointment and relief, focus on protagonist's reaction to the fortune telling."},
        {"role": "user", "content": "적에게 계속 도망치면서 세상을 구할 목표를 향해 팀원들과 향해 나아간다. 모험중에서 새로운 사람도 만나며 나아가지만 결국 나 혼자서 해내야 하는 상황에 마주친다. 하지만 목표를 향한 문제 풀이 과정에서 답도 모르지만 안풀리는 상황에 놓이고 적에게 붙잡히지는 않았지만 따라잡히게 된다."},
        {"role": "system", "content": "Hero's journey, digital art, illustration, Adventure to save world, Dramatic adventure lighting, Vivid fantasy colors, Determination and anxiety, Spotlight on the lone struggle and pursuit."},
        {"role": "user", "content": message}
    ]
    prompt = await send_gpt_request(messages_prompt)
    dream_image_url = await save_image(image_model, prompt)
    return dream_image_url

async def save_image(image_model: int, prompt: str):
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
    buffer.getvalue()

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
        bucket_image_url = blob.public_url
    return bucket_image_url
