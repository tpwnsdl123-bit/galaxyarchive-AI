from app.models.base import BaseEmbeddingModel
from sentence_transformers import SentenceTransformer
import time

print("BGE-M3 모델 로딩 시작합니다.")
model = SentenceTransformer('BAAI/bge-m3')
print("BGE-M3 모델 로딩을 완료했습니다.")

# 임베딩 모델 클래스
class DenseEmbeddingModel(BaseEmbeddingModel):

    def __init__(self):
        pass

    # 임베딩 추론 함수
    def embed_text(self, text: str):
        start_time = time.time()
        embedding = model.encode(text)
        end_time = time.time()
        cal_time = end_time - start_time
        print(f"순수 임베딩 연산 소요 시간 : {cal_time:.4f}초")
        return embedding