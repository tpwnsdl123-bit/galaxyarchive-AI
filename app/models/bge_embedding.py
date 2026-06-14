from app.models.base import BaseEmbeddingModel
from sentence_transformers import SentenceTransformer
import time

# 임베딩 모델 클래스
class DenseEmbeddingModel(BaseEmbeddingModel):
    _instance = None

    def __new__(cls, *args, **kwargs): #args kwargs 어떤 키워드는 어떤 형식이든 다 받겠다
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance        

    def __init__(self):
        if self._initialized:
            return
        
        print("BGE-M3 모델 로딩 시작합니다.")
        self.model = SentenceTransformer('BAAI/bge-m3')
        print("BGE-M3 모델 로딩을 완료했습니다.")

        self._initialized = True

    # 임베딩 추론 함수
    def embed_text(self, text: str):
        start_time = time.time()
        embedding = self.model.encode(text)
        end_time = time.time()
        cal_time = end_time - start_time
        print(f"순수 임베딩 연산 소요 시간 : {cal_time:.4f}초")
        return embedding