from database.database import get_session
from repository.article_cluster_repository import ArticleClusterRepository, ArticleDimension


def article_cluster_persist(user_id: str, article_dimensions: list[ArticleDimension]) -> None:
    with get_session() as session:
        ArticleClusterRepository(session).save_user_article_clusters(user_id, article_dimensions)
