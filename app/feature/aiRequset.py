import openai
from aiohttp import ClientSession
from dotenv import load_dotenv
from bardapi import Bard
import os
load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")
os.environ['_BARD_API_KEY']=os.getenv("BARD_API_KEY")
stable_diffusion_api_key = os.getenv("STABLE_DIFFUSION")
bard = Bard(timeout=30)

async def send_gpt_request(messages_prompt, retries=3):
    for i in range(retries):
        try:
            chat = openai.ChatCompletion.create(model="gpt-4", messages=messages_prompt)
            return chat.choices[0].message.content
        except:
            print("GPT API Error")
            if i < retries - 1:
                print(f"Retrying {i + 1} of {retries}...")
            else:
                print("Failed to get response after maximum retries")
                return "ERROR"

async def send_bard_request(messages_prompt, retries=3):
    for i in range(retries):
        try:
            return bard.get_answer(messages_prompt)['content']
        except:
            print("Bard API Error")
            if i < retries - 1:
                print(f"Retrying {i + 1} of {retries}...")
            else:
                print("Failed to get response after maximum retries")
                return "ERROR"

async def send_stable_deffusion_request(messages_prompt, retries=3):
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
                    print(result)
                    return result["output"][0]
        except:
            print("Stable Diffusion API Error")
            if i < retries - 1:
                print(f"Retrying {i + 1} of {retries}...")
            else:
                print("Failed to get response after maximum retries")
                return "ERROR"