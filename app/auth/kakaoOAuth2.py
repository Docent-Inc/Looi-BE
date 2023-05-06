import requests
from fastapi import HTTPException
from httpx_oauth.errors import GetIdEmailError
from dotenv import load_dotenv
import os

load_dotenv()
CLIENT_ID = os.getenv("KAKAO_API_KEY")
CLIENT_SECRET = os.getenv("KAKAO_API_SECRET")
# REDIRECT_URI = "https://bmongsmong.com/api/auth/kakao/callback"
REDIRECT_URI = "http://localhost:3000/kakao"
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
        raise HTTPException(status_code=400, detail="Could not get user info")