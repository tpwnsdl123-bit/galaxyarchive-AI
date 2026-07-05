import logging
from uuid import UUID

from consumer.kafka_consumer import kafka_consumer
from consumer.worker import handler
from database.database import get_session
from article_cluster.service.persist_cluster_service import article_cluster_persist
from repository.article_cluster_repository import ArticleDimension
from repository.article_vector_repository import ArticleVectorRepository
from article_cluster.service.cluster_service import cluster_dimensions
from article_cluster.service.reduce_dimension_service import reduce_dimension


@handler("article-user-cluster")
def article_user_cluster_handler(msg)->None:
    user_id = _extract_user_id(msg)
    if user_id is None:
        logging.warning("user id is undefined or invalid uuid: %s", msg)
        kafka_consumer.commit()
        return

    try:
        with get_session() as session:
            user_article_vecs = ArticleVectorRepository(session).find_all_article_vector_by_author(user_id)

        vectors = [article_vec["vector"] for article_vec in user_article_vecs]
        dimensions = reduce_dimension(vectors)
        cluster_results = cluster_dimensions(dimensions)
        article_dimensions: list[ArticleDimension] = [
            {
                "article_id": article_vec["article_id"],
                "dimension": dimension,
                "cluster_id": cluster_result["cluster_id"],
                "probability": cluster_result["probability"],
                "outlier_score": cluster_result["outlier_score"],
            }
            for article_vec, dimension, cluster_result in zip(user_article_vecs, dimensions, cluster_results)
        ]

        article_cluster_persist(user_id, article_dimensions)
        kafka_consumer.commit()

    except Exception as e:
        logging.error(e)
        kafka_consumer.commit()


def _extract_user_id(msg) -> str | None:
    user_id = msg.get("userId") if isinstance(msg, dict) else msg
    if not isinstance(user_id, str) or not user_id.strip():
        return None

    try:
        return str(UUID(user_id))
    except ValueError:
        return None
