
from database.database import get_session
from repository.article_repository import ArticleRepository
import logging


def get_article(article_id:int,status:str)->dict:
    with get_session() as session:
        article_repository = ArticleRepository(session)
        article = article_repository.get_article_with_status(article_id,status)
        if article is None:
            logging.error(f"valid article {article_id} not found")
            raise Exception(f"Article with id {article_id} does not exist")
        return article
