import sys
print("--- sys.path ---")
for p in sys.path:
    print(p)
print("----------------")

import os
import sys
from contextlib import asynccontextmanager

# 프로젝트 루트 추가
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn
from fastapi import FastAPI
from app.db.db_connection import test_connection
from app.messaging.KafkaConsumerManager import KafkaConsumerManager
from app.article.router.article_router import router as article_router
from app.article.handler import article_handler


kafka_consumer_manager = KafkaConsumerManager()


@asynccontextmanager
async def lifespan(app: FastAPI):


    test_connection()
 
    # 이벤트 구독
    kafka_consumer_manager.start([
        "article-events",
    ])

    yield

    #카프카 컨슈머 종료
    kafka_consumer_manager.stop()

    print("Kafka Consumer Stopped")


app = FastAPI(
    title="Galaxy Archive AI API",
    lifespan=lifespan
)

# 라우터 등록
app.include_router(article_router)




@app.get("/")
def health_check():
    return {"status": "OK"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
