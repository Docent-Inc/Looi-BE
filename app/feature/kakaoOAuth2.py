import requests
from fastapi import HTTPException, status
from httpx_oauth.errors import GetIdEmailError
from app.core.config import settings

CLIENT_ID = settings.KAKAO_API_KEY
CLIENT_SECRET = settings.KAKAO_CLIENT_SECRET
REDIRECT_URI = "https://docent.zip/callback"
REDIRECT_URI_TEST = "http://localhost:3000/callback"
REDIRECT_URI_VERCEL = "https://docent-front.vercel.app/callback"
KAKAO_AUTH_URL_TEST = f"https://kauth.kakao.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI_TEST}&response_type=code"
KAKAO_AUTH_URL = f"https://kauth.kakao.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
KAKAO_AUTH_URL_VERCEL = f"https://kauth.kakao.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI_VERCEL}&response_type=code"
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

async def get_user_kakao_vercel(request: str):
    try:
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI_VERCEL,
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