import requests
from dotenv import load_dotenv
import os
import random

from fastapi import HTTPException, status
from httpx_oauth.errors import GetIdEmailError

load_dotenv()

LINE_CHANNEL_ID = os.getenv("LINE_CHANNEL_ID")
REDIRECT_URI = "https://docent.zip/line"
LINE_SECRET = os.getenv("LINE_SECRET")
PROFILE_ENDPOINT = "https://api.line.me/v2/profile"
REDIRECT_URI_TEST = "http://localhost:3000/line"
LINE_AUTH_URL = f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={LINE_CHANNEL_ID}&redirect_uri={REDIRECT_URI}&state={random.randint(1000000000, 9999999999)}&scope=profile%20openid%20email"
LINE_AUTH_URL_TEST = f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={LINE_CHANNEL_ID}&redirect_uri={REDIRECT_URI_TEST}&state={random.randint(1000000000, 9999999999)}&scope=profile%20openid%20email"

async def get_user_line(request: str):
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": LINE_CHANNEL_ID,
            "client_secret": LINE_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": request,
        }
        response = requests.get("https://api.line.me/oauth2/v2.1/token", data=data)

        token = response.json().get("access_token")
        print(token)

        # headers = {"Authorization": f"Bearer {token}"}
        # user_info = requests.get(PROFILE_ENDPOINT, headers=headers).json()
        # return user_info
    except GetIdEmailError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4010,
        )

async def get_user_line_test(request: str):
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": LINE_CHANNEL_ID,
            "client_secret": LINE_SECRET,
            "redirect_uri": REDIRECT_URI_TEST,
            "code": request,
        }
        response = requests.post("https://api.line.me/oauth2/v2.1/token", data=data)

        token = response.json().get("access_token")

        headers = {"Authorization": f"Bearer {token}"}
        user_info = requests.get(PROFILE_ENDPOINT, headers=headers).json()
        return user_info
    except GetIdEmailError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4010,
        )