from repository.article_vector_repository import ArticleVectorRepository
from repository.article_keyword_repository import ArticleKeywordRepository
from database.database import get_session

import logging

def article_embedding_persist(article_id, vecs:list[float], keywords:list[tuple[str,float]]):
    try:
        with get_session() as session:
            article_vector_repository = ArticleVectorRepository(session)
            article_keyword_repository = ArticleKeywordRepository(session)
            article_vector_repository.save_article_vector(article_id, vecs)
            article_keyword_repository.save_all(article_id, keywords)
    except Exception as e:
        logging.exception(e)
        raise e