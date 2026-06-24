# galaxyArchive AI WORKER
## Overview
Galaxy Archive AI Worker는 Spring Application에서 발행한 이벤트를 소비하여 게시글 분석 작업을 수행하는 독립적 워커입니다.

기존 Ollama가 담당하던 게시글 임베딩 생성 및 키워드 추출 기능을 분리하여 비동기 이벤트 기반으로 처리하며, 대용량 데이터 분석 및 배치 작업을 담당합니다.

---
### Features
- Apache Kafka 기반 비동기 이벤트 처리
- BGE-M3 모델을 활용한 게시글 임베딩 벡터 생성
- Kiwi 형태소 분석기를 활용한 핵심 키워드 추출 및 키워드 임베딩 게시글과 코사인 유사도를 이용 키워드 관련도 산출
- Docker기반 컨테이너 환경
- uv 를 통한 프로젝트 의존성 및 가상환경 관리
---
### Requirements
| Tool | Version |
|--------|--------|
| Python | 3.12.11 |
| uv | 0.8.13 |
---
### EnvironmentVariable
```
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 #kafka bootstrap
KAFKA_GROUP_ID=embedding-worker #cunsumer id
ROOT_MODEL_DIR=./models #컨테이너 내부, 로컬 구동시 모델 캐싱 경로
LOG_LEVEL=DEBUG # 로그레벨
```

---
#### Install Dependencies
> uv sync

### Run
Local Development
> uv run python main.py

Docker Compose
> docker compose up -d

