import openai
from dotenv import load_dotenv
from bardapi import Bard
import os
load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")
os.environ['_BARD_API_KEY']=os.getenv("BARD_API_KEY")
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