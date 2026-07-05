import hdbscan
from typing import TypedDict


class ClusterResult(TypedDict):
    cluster_id: int
    probability: float
    outlier_score: float


def cluster_dimensions(dimensions: list[list[float]]) -> list[ClusterResult]:
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2,
        min_samples=1,
    )

    clusterer.fit(dimensions)

    return [
        {
            "cluster_id": int(cluster_id),
            "probability": float(probability),
            "outlier_score": float(outlier_score),
        }
        for cluster_id, probability, outlier_score in zip(
            clusterer.labels_,
            clusterer.probabilities_,
            clusterer.outlier_scores_,
        )
    ]
