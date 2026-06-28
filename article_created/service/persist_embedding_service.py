from article_created.repository.article_vector_repository import save_article_vector
from article_created.repository.article_keyword_repository import save_article_keyword
from database.database import get_session

import logging

def article_embedding_persist(article_id, vecs:list[float], keywords:list[tuple[str,float]]):
    try:
        with get_session() as session:
            save_article_vector(session, article_id, vecs)
            save_article_keyword(session, article_id, keywords)
    except Exception as e:
        logging.exception(e)
        raise e