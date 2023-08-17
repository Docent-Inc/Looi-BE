import openai
from aiohttp import ClientSession
from dotenv import load_dotenv
from fastapi import HTTPException
import os
load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")
stable_diffusion_api_key = os.getenv("STABLE_DIFFUSION")
hyperclova_api_key = os.getenv("HYPER_CLOVA_KEY")
hyperclova_api_gateway = os.getenv("HYPER_CLOVA_GATEWAY")
hyperclova_request_id = os.getenv("HYPER_CLOVA_REQUEST_ID")
kakao_api_key = os.getenv("KAKAO_API_KEY")

async def send_gpt_request(messages_prompt, retries=3):
    '''
    주어진 프롬프트로 GPT API에 요청을 보내고, 실패할 경우 3번까지 재시도합니다.

    :param messages_prompt: 대화를 위한 메시지 객체들의 리스트입니다. 각 메시지 객체는 'role' ( 'system', 'user', 'assistant' 중 하나)과 'content' (해당 역할로부터의 메시지 내용)를 가져야 합니다.
    :param retries: API 호출 실패시 요청을 재시도하는 횟수입니다.
    :return: 성공적이라면 GPT API로부터의 응답 내용, 실패라면 "ERROR"를 반환합니다.
    '''
    for i in range(retries):
        try:
            chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages_prompt)
            return chat.choices[0].message.content
        except Exception as e:
            print(f"GPT API Error {e}")
            if i < retries - 1:
                print(f"Retrying {i + 1} of {retries}...")
            else:
                print("Failed to get response after maximum retries")
                raise HTTPException(status_code=500, detail="GPT API Error")

async def send_hyperclova_request(messages_prompt, retries=3):
    '''
    주어진 프롬프트로 Hyperclova API에 요청을 보내고, 실패할 경우 3번까지 재시도합니다.

    :param messages_prompt: hyperclova API에 보낼 문자열로 이루어진 프롬프트입니다.
    :param retries: API 호출 실패시 요청을 재시도하는 횟수입니다.
    :return: 성공적이라면 hyperclova API로부터의 응답 내용, 실패라면 "ERROR"를 반환합니다.
    '''
    for i in range(retries):
        try:
            url = "https://clovastudio.apigw.ntruss.com/serviceapp/v1/tasks/x56n5fyu/completions/LK-D2"

            request_data = {
                'text': messages_prompt,
                'maxTokens': 1200,
                'temperature': 0.7,
                'topK': 0,
                'topP': 0.8,
                'repeatPenalty': 8.0,
                'start': '###클로바:',
                'restart': '',
                'stopBefore': ['###꿈 내용:'],
                'includeTokens': True,
                'includeAiFilters': True,
                'includeProbs': False
            }

            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                "X-NCP-CLOVASTUDIO-API-KEY": hyperclova_api_key,
                "X-NCP-APIGW-API-KEY": hyperclova_api_gateway,
            }

            async with ClientSession() as session:
                async with session.post(url, headers=headers, json=request_data) as response:
                    result = await response.json()
                    return result['result']['text']
        except Exception as e:
            print(f"Hypercolva API Error: {e}")
            if i < retries - 1:
                print(f"Retrying {i + 1} of {retries}...")
            else:
                print("Failed to get response after maximum retries")
                raise HTTPException(status_code=500, detail="Hyperclova API Error")
async def send_stable_deffusion_request(messages_prompt, retries=3):
    '''
    주어진 프롬프트로 Stable Diffusion API에 요청을 보내고, 실패할 경우 3번까지 재시도합니다.

    :param messages_prompt: stable diffusion API에 보낼 문자열로 이루어진 프롬프트입니다.
    :param retries: API 호출 실패시 요청을 재시도하는 횟수입니다.
    :return: 성공적이라면 stable diffusion API로부터의 응답 내용, 실패라면 "ERROR"를 반환합니다.
    '''
    for i in range(retries):
        try:
            url = "https://stablediffusionapi.com/api/v3/text2img"

            data = {
                "key": stable_diffusion_api_key,
                "prompt": messages_prompt[:300],
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
                    result = await response.json()
                    return result["output"][0]
        except Exception as e:
            print(f"Stable Diffusion API Error{e}")
            if i < retries - 1:
                print(f"Retrying {i + 1} of {retries}...")
            else:
                print("Failed to get response after maximum retries")
                raise HTTPException(status_code=500, detail="Stable Diffusion API Error")

async def send_karlo_request(messages_prompt, retries=3):
    '''
    주어진 프롬프트로 Karlo API에 요청을 보내고, 실패할 경우 3번까지 재시도합니다.

    :param messages_prompt: karlo API에 보낼 문자열로 이루어진 프롬프트입니다.
    :param retries: API 호출 실패시 요청을 재시도하는 횟수입니다.
    :return: 성공적이라면 karlo API로 만들어진 이미지 url, 실패라면 "ERROR"를 반환합니다.
    '''
    for i in range(retries):
        try:
            url = "https://api.kakaobrain.com/v2/inference/karlo/t2i"

            data = {
                'prompt': messages_prompt[:255],
                'prior_guidance_scale': 5,
                'width': '512',
                'height': '512',
                'nsfw_checker': True,
            }

            headers = {
                'Authorization': f'KakaoAK {kakao_api_key}',
                'Content-Type': 'application/json'
            }

            async with ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    return result['images'][0]['image']
        except Exception as e:
            print(f"Karlo API Error{e}")
            if i < retries - 1:
                print(f"Retrying {i + 1} of {retries}...")
            else:
                print("Failed to get response after maximum retries")
                raise HTTPException(status_code=500, detail="Karlo API Error")


