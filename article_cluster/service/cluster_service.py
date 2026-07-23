import hdbscan
from typing import TypedDict
import math

class ClusterResult(TypedDict):
    cluster_id: int
    probability: float
    outlier_score: float


def cluster_dimensions(dimensions: list[list[float]]) -> list[ClusterResult]:
    if len(dimensions) < 3:
        return [
            {
                "cluster_id": -1,
                "probability": 0.0,
                "outlier_score": 0.0,
            }
            for _ in dimensions
        ]

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2,
        min_samples=3,
        cluster_selection_method="eom"
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
