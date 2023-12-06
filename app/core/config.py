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
    class Config:
        # 개발 환경은 ".env-dev" 파일
        # 서버 환경은 ".env" 파일
        env_file = ".env-dev"

settings = Settings()
