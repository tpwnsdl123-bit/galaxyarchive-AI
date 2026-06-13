import os
import sys

#TODO-: 프로젝트 루트 디렉토리를 sys.path에 추가하여 모듈 원리
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn
from fastapi import FastAPI

from app.article.router.article_router import router as article_router

app = FastAPI(title="Galaxy Archive AI API")

# 라우터 등록
app.include_router(article_router)

@app.get("/")
def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)