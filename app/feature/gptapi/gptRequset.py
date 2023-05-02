import openai
from dotenv import load_dotenv
import os
load_dotenv()
openai.api_key = os.getenv("GPT_API_KEY")

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