from sqlalchemy.orm import Session
from sqlalchemy import text


class ArticleRepository:
    def __init__(self, session: Session):
        self.session = session

    def is_exist_article_with_status(self, article_id: int, status:str) -> bool:
        result = self.session.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM article
                    WHERE id = :article_id
                    AND is_deleted = false
                    AND status = :status
                )
            """),
            {"article_id": article_id, "status": status}
        )
        return bool(result.scalar())

    def get_article_with_status(self, article_id: int,status:str)->dict|None:
        result = self.session.execute(
            text("""
            SELECT title,raw_text,text
                FROM article
                WHERE id = :article_id
                AND is_deleted = false
                AND status = :status
            """),
            {"article_id": article_id, "status": status}
        )
        row = result.mappings().first()

        if row is None:
            return None
        return dict(row)