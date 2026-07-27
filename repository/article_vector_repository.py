from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import TypedDict
import json

class ArticleVectorRow(TypedDict):
    article_id: int
    title: str
    vector: list[float]
    keywords: list[str]

class ArticleVectorRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_article_vector(self, article_id:int , article_vector: list[float])->None:
        self.session.execute(text(
            """
        INSERT INTO article_vector (article_id, updated_at, vector)
        VALUES (:article_id, NOW(), :article_vector)
        """
        ),{"article_id":article_id, "article_vector":article_vector})

    def find_all_article_vector_by_author(self, user_id: str) -> list[ArticleVectorRow]:
        result = self.session.execute(
            text("""
                 SELECT vector.article_id AS article_id,
                        article.title AS title,
                        vector.vector AS vector,
                        COALESCE(
                            json_agg(keyword.keyword) FILTER (WHERE keyword.keyword IS NOT NULL),
                            '[]'
                        ) AS keywords
                 FROM article article
                          JOIN article_vector vector ON article.id = vector.article_id
                          LEFT JOIN article_keyword keyword ON article.id = keyword.article_id
                 WHERE article.author_id = :user_id
                   AND article.is_deleted = false
                 GROUP BY vector.article_id, article.title, vector.vector;
                 """),
            {"user_id": user_id}
        )
        return [
            {
                "article_id": row["article_id"],
                "title": row["title"],
                "vector": json.loads(row["vector"]),
                "keywords": _json_or_value(row["keywords"]),
            }
            for row in result.mappings()
        ]


def _json_or_value(value):
    if isinstance(value, str):
        return json.loads(value)

    return value
