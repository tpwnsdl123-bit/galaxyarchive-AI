from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import cast

class ArticleVectorRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_article_vector(self, article_id:int , article_vector: list[float])->None:
        self.session.execute(text(
            """
        INSERT INTO article_vector_entity (article_id, updated_at, vector)
        VALUES (:article_id, NOW(), :article_vector)
        """
        ),{"article_id":article_id, "article_vector":article_vector})

    def find_all_article_vector_by_author(self, user_id: str) -> list[list[float]]:
        result = self.session.execute(
            text("""
                 SELECT vector
                 FROM article_entity article
                          JOIN article_vector_entity vector ON article.id = vector.article_id
                 WHERE article.author_id = :user_id;
                 """),
            {"user_id": user_id}
        )
        return cast(list[list[float]], result.scalars().all())