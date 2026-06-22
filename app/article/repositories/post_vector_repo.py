from sqlalchemy import text

class PostVectorRepository:
    def __init__(self, db):
        self.db = db

    def save_article_vector(self, article_id: int, vector: list):
        try:
            vector_str = str(vector)# 파이썬 리스트 데이터를 표준 텍스트 벡터 포맷으로 치환

            self.db.execute(
                text("""
                    INSERT INTO article_vector_entity (article_id, updated_at, vector)
                    VALUES (:article_id, NOW(), :vector)
                """),
                {"article_id": article_id, "vector":vector_str}
            )
            self.db.commit()
            print(f"[DB] Article Vector 저장 완료 - ID : {article_id}")
            return True
        except Exception as e: # 에러 발생 시 디비 롤벡하고 로그 출력
            self.db.rollback()
            print(f"Error save article vector: {e}")
            return False
        