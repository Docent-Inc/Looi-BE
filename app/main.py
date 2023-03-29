from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

templates = Jinja2Templates(directory="templates")

app = FastAPI(docs_url="/documentation", redoc_url=None)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html",{"request":request})