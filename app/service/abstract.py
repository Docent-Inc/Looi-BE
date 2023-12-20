from pydantic import BaseModel
from abc import ABC, abstractmethod

from app.db.models import User


class AbstractDiaryService(ABC):
    @abstractmethod
    async def create(self, data: BaseModel) -> object:
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
    async def list(self, page: int) -> list:
        pass

class AbstractShareService(ABC):
    @abstractmethod
    async def dream_read(self, id: int) -> object:
        pass

    @abstractmethod
    async def diary_read(self, id: int) -> object:
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
    async def delete(self, id: int) -> None:
        pass

    @abstractmethod
    async def list(self, page: int) -> list:
        pass

class AbstractAuthService(ABC):
    @abstractmethod
    async def login(self, service: str, env: str) -> str:
        pass

    @abstractmethod
    async def callback(self, service: str, env: str, code: str) -> object:
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
    async def luck(self) -> object:
        pass

    @abstractmethod
    async def history(self) -> object:
        pass

    @abstractmethod
    async def calendar(self) -> object:
        pass