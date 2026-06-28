from sqlalchemy.orm import Session
from sqlalchemy import text

def is_exist_article(session: Session, article_id: int) -> bool:
    result = session.execute(
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