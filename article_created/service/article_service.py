
from article_created.repository.article_repository import is_exist_article
from database.database import get_session

def validate_article(article_id:int)->bool:
    with get_session() as session:
        return is_exist_article(session, article_id)