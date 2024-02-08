from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    GPT_API_KEY: str
    GOOGLE_APPLICATION_CREDENTIALS_JSON: str
    LINE_CHANNEL_ID: str
    LINE_SECRET: str
    TEST_TOKEN: str
    DB_ADDRESS: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    KAKAO_API_KEY: str
    KAKAO_CLIENT_SECRET: str
    ROOT_PATH: str
    MAX_LENGTH: int
    MAX_CALL: int
    SLACK_ID: str
    SLACK_BOT_TOKEN: str
    WEATHER_API_KEY: str
    SERVER_TYPE: str
    APPLE_LOGIN_KEY: str
    KAKAO_REDIRECT_URI_LOCAL: str
    KAKAO_REDIRECT_URI_DEV: str
    KAKAO_REDIRECT_URI_PROD: str
    LINE_REDIRECT_URI_LOCAL: str
    LINE_REDIRECT_URI_DEV: str
    LINE_REDIRECT_URI_PROD: str
    APPLE_REDIRECT_URI_DEV: str
    APPLE_REDIRECT_URI_PROD: str
    NAVER_CLOUD_ACCESS_KEY_ID: str
    NAVER_CLOUD_SECRET_KEY: str
    FIREBASE_API_KEY: str
    FIREBASE_JSON: str
    NAVER_API_KEY: str
    NAVER_GATEWAY_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
