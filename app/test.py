from sentence_transformers import SentenceTransformer
import time

model = SentenceTransformer('BAAI/bge-m3')

sample_text = "안녕하세요 모델 테스트입니다. 앞으로의 프로젝트가 기대됩니다."

start_time = time.time()

embedding = model.encode(sample_text)

end_time = time.time()
cal_time = end_time - start_time

print("임베딩 벡터 추출 성공")
print("벡터 차원 수 : ", len(embedding))
print("앞부분 데이터 일부:", embedding[:5])

print(f"연산 소요 시간 : {cal_time:.4f}초")