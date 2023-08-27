import requests
from fastapi import HTTPException, status
from httpx_oauth.errors import GetIdEmailError
from dotenv import load_dotenv
import os

load_dotenv()
CLIENT_ID = os.getenv("KAKAO_API_KEY")
CLIENT_SECRET = os.getenv("KAKAO_API_SECRET")
REDIRECT_URI = "https://docent.zip/kakao"
REDIRECT_URI_TEST = "http://localhost:3000/kakao"
KAKAO_AUTH_URL_TEST = f"https://kauth.kakao.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI_TEST}&response_type=code"
KAKAO_AUTH_URL = f"https://kauth.kakao.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
AUTHORIZE_ENDPOINT = "https://kauth.kakao.com/oauth/authorize"
ACCESS_TOKEN_ENDPOINT = "https://kauth.kakao.com/oauth/token"
PROFILE_ENDPOINT = "https://kapi.kakao.com/v2/user/me"
BASE_SCOPES = ["account_email"]
BASE_PROFILE_SCOPES = ["kakao_account.email"]

async def get_user_kakao(request: str):
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code": request,
        }
        response = requests.post(ACCESS_TOKEN_ENDPOINT, data=data)
        token = response.json().get("access_token")

        headers = {"Authorization": f"Bearer {token}"}
        user_info = requests.get(PROFILE_ENDPOINT, headers=headers).json()
        return user_info
    except GetIdEmailError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4010,
        )

async def get_user_kakao_test(request: str):
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI_TEST,
            "code": request,
        }
        response = requests.post(ACCESS_TOKEN_ENDPOINT, data=data)
        token = response.json().get("access_token")

        headers = {"Authorization": f"Bearer {token}"}
        user_info = requests.get(PROFILE_ENDPOINT, headers=headers).json()
        return user_info
    except GetIdEmailError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=4010,
        )