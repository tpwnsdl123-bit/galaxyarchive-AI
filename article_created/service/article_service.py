
from database.database import get_session
from repository.article_repository import ArticleRepository
import logging

def validate_article(article_id:int)->bool:
    with get_session() as session:
        article_repository = ArticleRepository(session)
        return article_repository.is_exist_article(article_id)

def get_article(article_id:int)->dict:
    with get_session() as session:
        article_repository = ArticleRepository(session)
        article = article_repository.get_article(article_id)
        if article is None:
            logging.error(f"valid article {article_id} not found")
            raise Exception(f"Article with id {article_id} does not exist")
        return article
