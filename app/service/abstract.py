from pydantic import BaseModel
from abc import ABC, abstractmethod
from fastapi import BackgroundTasks, Response
from app.db.models import User


class AbstractDiaryService(ABC):
    @abstractmethod
    async def create(self, data: BaseModel) -> object:
        pass

    @abstractmethod
    async def generate(self, id: int) -> object:
        pass

    @abstractmethod
    async def read(self, id: int) -> object:
        pass

    @abstractmethod
    async def update(self, id: int, data: BaseModel) -> object:
        pass

    @abstractmethod
    async def delete(self, id: int) -> None:
        pass

    @abstractmethod
    async def list(self, page: int, background_tasks: BackgroundTasks) -> list:
        pass

class AbstractShareService(ABC):
    @abstractmethod
    async def read(self, id: int) -> object:
        pass

class AbstractChatService(ABC):
    @abstractmethod
    async def create(self, data: BaseModel) -> object:
        pass

    @abstractmethod
    async def welcome(self, text_type: int) -> object:
        pass

    @abstractmethod
    async def helper(self, text_type: int) -> object:
        pass

class AbstractStatisticsService(ABC):
    @abstractmethod
    async def ratio(self) -> object:
        pass

class AbstractReportService(ABC):
    @abstractmethod
    async def read(self, id: int) -> dict:
        pass

    @abstractmethod
    async def list(self, page: int) -> list:
        pass

    @abstractmethod
    async def generate(self) -> object:
        pass

class AbstractAuthService(ABC):
    @abstractmethod
    async def login(self, service: str, env: str) -> str:
        pass

    @abstractmethod
    async def callback(self, service: str, env: str, code: str, response: Response) -> object:
        pass

    @abstractmethod
    async def refresh(self, refresh_token: str) -> object:
        pass

    @abstractmethod
    async def info(self, user: User) -> object:
        pass

    @abstractmethod
    async def update(self, data: BaseModel, user: User) -> None:
        pass

    @abstractmethod
    async def update_push(self, data: BaseModel, user: User) -> None:
        pass

    @abstractmethod
    async def delete(self, user: User) -> None:
        pass

class AbstractTodayService(ABC):
    @abstractmethod
    async def luck(self) -> dict:
        pass

    @abstractmethod
    async def history(self) -> dict:
        pass

    @abstractmethod
    async def calendar(self) -> object:
        pass

    @abstractmethod
    async def weather(self, x: float, y: float) -> dict:
        pass

class AbstractAdminService(ABC):
    @abstractmethod
    async def user_list(self) -> list:
        pass

    @abstractmethod
    async def dashboard(self) -> list:
        pass

    @abstractmethod
    async def user_dream_data(self) -> list:
        pass

    @abstractmethod
    async def user_diary_data(self) -> list:
        pass

    @abstractmethod
    async def slack_bot(self) -> dict:
        pass

class AbstractPushService(ABC):
    @abstractmethod
    async def test(self, title: str, body: str, landing_url: str, image_url: str, token: str, device: str) -> None:
        pass
    @abstractmethod
    async def send(self, title: str, body: str, token: str, device: str) -> None:
        pass