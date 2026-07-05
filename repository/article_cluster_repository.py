from collections import Counter
from typing import TypedDict
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


class ArticleDimension(TypedDict):
    article_id: int
    dimension: list[float]
    cluster_id: int
    probability: float
    outlier_score: float


class ArticleClusterRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_user_article_clusters(self, user_id: str, article_dimensions: list[ArticleDimension]) -> None:
        if not article_dimensions:
            return

        snapshot_id = self._save_snapshot(user_id, article_dimensions)
        cluster_ids_by_label = self._save_clusters(snapshot_id, article_dimensions)
        self._save_cluster_articles(article_dimensions, cluster_ids_by_label)

    def _save_snapshot(self, user_id: str, article_dimensions: list[ArticleDimension]) -> int:
        labels = {article_dimension["cluster_id"] for article_dimension in article_dimensions}
        cluster_count = len([label for label in labels if label != -1])

        result = self.session.execute(
            text("""
                 INSERT INTO user_cluster_snapshot_entity
                     (algorithm, article_count, cluster_count, created_at, run_id, status, user_id)
                 VALUES
                     (:algorithm, :article_count, :cluster_count, NOW(), :run_id, :status, :user_id)
                 RETURNING id
                 """),
            {
                "algorithm": "UMAP_HDBSCAN",
                "article_count": len(article_dimensions),
                "cluster_count": cluster_count,
                "run_id": str(uuid4()),
                "status": "COMPLETED",
                "user_id": user_id,
            },
        )

        return result.scalar_one()

    def _save_clusters(
        self,
        snapshot_id: int,
        article_dimensions: list[ArticleDimension],
    ) -> dict[int, int]:
        article_counts_by_label = Counter(
            article_dimension["cluster_id"]
            for article_dimension in article_dimensions
        )

        cluster_ids_by_label: dict[int, int] = {}
        for label, article_count in article_counts_by_label.items():
            result = self.session.execute(
                text("""
                     INSERT INTO user_cluster_entity
                         (article_count, is_noise, label, snapshot_id)
                     VALUES
                         (:article_count, :is_noise, :label, :snapshot_id)
                     RETURNING id
                     """),
                {
                    "article_count": article_count,
                    "is_noise": label == -1,
                    "label": label,
                    "snapshot_id": snapshot_id,
                },
            )
            cluster_ids_by_label[label] = result.scalar_one()

        return cluster_ids_by_label

    def _save_cluster_articles(
        self,
        article_dimensions: list[ArticleDimension],
        cluster_ids_by_label: dict[int, int],
    ) -> None:
        params = [
            {
                "article_id": article_dimension["article_id"],
                "cluster_id": cluster_ids_by_label[article_dimension["cluster_id"]],
                "x": article_dimension["dimension"][0],
                "y": article_dimension["dimension"][1],
                "z": article_dimension["dimension"][2],
                "probability": article_dimension["probability"],
                "outlier_score": article_dimension["outlier_score"],
            }
            for article_dimension in article_dimensions
        ]

        self.session.execute(
            text("""
                 INSERT INTO cluster_article_entity
                     (article_id, cluster_id, x, y, z, probability, outlier_score)
                 VALUES
                     (:article_id, :cluster_id, :x, :y, :z, :probability, :outlier_score)
                 """),
            params,
        )
