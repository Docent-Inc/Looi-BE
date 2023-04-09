from fastapi import FastAPI
from app.routers import gpt

app = FastAPI()

app.include_router(gpt.router, prefix="/gpt")

@app.get("/")
async def root():
    return {"message": "Hello World"}