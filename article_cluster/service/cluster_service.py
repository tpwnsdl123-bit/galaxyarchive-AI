import hdbscan


def cluster_dimensions(dimensions: list[list[float]]) -> list[int]:
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2,
        min_samples=1,
    )

    return clusterer.fit_predict(dimensions).tolist()
