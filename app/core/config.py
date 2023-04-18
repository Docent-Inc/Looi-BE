from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "YOUR_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config: # .env 파일에 저장된 secret key정보를 가져옴
        env_file = ".env"

settings = Settings()