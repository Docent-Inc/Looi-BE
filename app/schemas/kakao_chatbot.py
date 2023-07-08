from typing import Optional, List, Dict, Any
from pydantic import BaseModel

'''
카카오 챗봇을 위한 API 스키마
'''

class SimpleImage(BaseModel):
    imageUrl: str

class SimpleText(BaseModel):
    text: str

class Output(BaseModel):
    simpleImage: Optional[SimpleImage] = None
    simpleText: Optional[SimpleText] = None

class Template(BaseModel):
    outputs: list[Output]

class KakaoChatbotResponseCallback(BaseModel):
    version: str
    useCallback: Optional[bool] = None
    template: Optional[Template] = None

class KakaoChatbotResponse(BaseModel):
    version: str
    template: Template