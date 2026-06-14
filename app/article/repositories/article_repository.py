from sqlalchemy import text
from app.db.database import SessionLocal


class ArticleRepository:
    def __init__(self, db):
        self.db = db

    def get_article_by_id(self, article_id: int):
        try:
            result = self.db.execute(
                text("SELECT * FROM article_entity WHERE id = :id"),
                {"id": article_id}
            )
            return result.mappings().first()
        except Exception as e:
            print(f"Error occurred while fetching article: {e}")
            return None