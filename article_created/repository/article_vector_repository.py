from sqlalchemy.orm import Session
from sqlalchemy import text

def save_article_vector(session:Session, article_id:int , article_vector: list[float])->None:
    session.execute(text(
        """
    INSERT INTO article_vector_entity (article_id, updated_at, vector)
    VALUES (:article_id, NOW(), :article_vector)
    """
    ),{"article_id":article_id, "article_vector":article_vector})