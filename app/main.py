from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from database.mysql_connection import engine
from app.user.user_repository import Base

# 서버 시작 시 테이블 자동 생성
Base.metadata.create_all(bind=engine)

from app.user.user_router import user
from app.review.review_router import router as review
from app.config import PORT

app = FastAPI()
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

app.include_router(user)
app.include_router(review)

if __name__=="__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
