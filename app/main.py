from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi import Request
from typing import Optional
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
class GPTResponse(BaseModel):
    text: str
@app.get("/gpt/{text}", response_model=GPTResponse)
async def get_gpt_result(text: str) -> GPTResponse:
    generated_text = generate_text(text)
    return GPTResponse(text=generated_text)



