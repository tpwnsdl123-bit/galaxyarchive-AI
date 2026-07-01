
from database.database import get_session
from repository.article_repository import ArticleRepository


def validate_article(article_id:int)->bool:
    with get_session() as session:
        article_repository = ArticleRepository(session)
        return article_repository.is_exist_article(article_id)