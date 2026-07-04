from consumer.worker import handler
from database.database import get_session
from article_cluster.service.persist_cluster_service import article_cluster_persist
from repository.article_cluster_repository import ArticleDimension
from repository.article_vector_repository import ArticleVectorRepository
from article_cluster.service.cluster_service import cluster_dimensions
from article_cluster.service.reduce_dimension_service import reduce_dimension

import logging

@handler("article-user-cluster")
def article_user_cluster_handler(msg)->None:
    user_id: str = msg.get("userId") if isinstance(msg, dict) else msg
    try:
        with get_session() as session:
            user_article_vecs = ArticleVectorRepository(session).find_all_article_vector_by_author(user_id)

        vectors = [article_vec["vector"] for article_vec in user_article_vecs]
        dimensions = reduce_dimension(vectors)
        cluster_ids = cluster_dimensions(dimensions)
        article_dimensions: list[ArticleDimension] = [
            {
                "article_id": article_vec["article_id"],
                "dimension": dimension,
                "cluster_id": cluster_id,
            }
            for article_vec, dimension, cluster_id in zip(user_article_vecs, dimensions, cluster_ids)
        ]

        article_cluster_persist(user_id, article_dimensions)

    except Exception as e:
        logging.error(e)
