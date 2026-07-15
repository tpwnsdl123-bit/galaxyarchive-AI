from sqlalchemy.orm import Session
from sqlalchemy import text


class ArticleRepository:
    def __init__(self, session: Session):
        self.session = session

    def is_exist_article(self, article_id: int) -> bool:
        result = self.session.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM article_entity
                    WHERE id = :article_id
                    AND is_deleted = false
                )
            """),
            {"article_id": article_id}
        )
        return bool(result.scalar())

    def get_article(self, article_id: int)->dict|None:
        result = self.session.execute(
            text("""
            SELECT title,raw_text,text
                FROM article_entity
                WHERE id = :article_id
                AND is_deleted = false
            """),
            {"article_id": article_id}
        )
        row = result.mappings().first()

        if row is None:
            return None
        return dict(row)