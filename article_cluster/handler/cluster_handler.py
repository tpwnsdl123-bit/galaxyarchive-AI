from consumer.worker import handler
from database.database import get_session
from repository.article_vector_repository import ArticleVectorRepository
from article_cluster.service.reduce_dimension_service import reduce_dimension

import logging

@handler("article-user-cluster")
def article_created_handler(msg)->None:
    user_id:str = msg.get("userId")
    try:
        with get_session() as session:
            user_article_vecs = ArticleVectorRepository(session).find_all_article_vector_by_author(user_id)

        reduce_dimension(user_article_vecs)

    except Exception as e:
        logging.error(e)