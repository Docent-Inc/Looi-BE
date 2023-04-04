from typing import Union
import base64
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import openai
import requests
from PIL import Image
from io import BytesIO
import time

from app.chatGPT import generate_text

app = FastAPI()
class GPTResponse(BaseModel):
    dream: str
    dream_resolution: str
    image_url: str

@app.get("/")
async def root():
    return {"message": "Hello World"}
@app.get("/gpt/{text}", response_model=GPTResponse)
async def get_gpt_result(text: str) -> GPTResponse:
    dream, dream_resolution, image_url = generate_text(text)
    return GPTResponse(dream=dream, dream_resolution=dream_resolution, image_url=image_url)

