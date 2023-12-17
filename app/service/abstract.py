from pydantic import BaseModel
from abc import ABC, abstractmethod

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