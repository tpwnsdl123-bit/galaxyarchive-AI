import os

from umap import UMAP

UMAP_CLUSTER_COMPONENTS = int(os.getenv(
    "UMAP_CLUSTER_COMPONENTS",
    "0",
))
UMAP_CLUSTER_MAX_COMPONENTS = int(os.getenv(
    "UMAP_CLUSTER_MAX_COMPONENTS",
    "50",
))
UMAP_CLUSTER_NEIGHBORS = int(os.getenv(
    "UMAP_CLUSTER_NEIGHBORS",
    "8",
))
UMAP_CLUSTER_MIN_DIST = float(os.getenv(
    "UMAP_CLUSTER_MIN_DIST",
    "0.1",
))
UMAP_VIEW_NEIGHBORS = int(os.getenv(
    "UMAP_VIEW_NEIGHBORS",
    "8",
))


def reduce_dimension(
    vecs: list[list[float]],
    n_components: int,
    min_dist: float,
    n_neighbors: int,
) -> list[list[float]]:
    if not vecs:
        return []

    reduced_vecs = _fallback_dimensions(len(vecs), n_components)
    valid_vecs = [
        (index, vec)
        for index, vec in enumerate(vecs)
        if not _is_zero_vector(vec)
    ]

    if len(valid_vecs) < 3:
        return reduced_vecs

    safe_components = min(n_components, len(valid_vecs) - 2)
    if safe_components < 1:
        return reduced_vecs

    reducer = UMAP(
        n_components=safe_components,
        n_neighbors=min(n_neighbors, len(valid_vecs) - 1),
        min_dist=min_dist,
        metric="cosine",
        init="random",
        n_jobs=1,
        random_state=42,
    )

    transformed_vecs = reducer.fit_transform([
        vec
        for _, vec in valid_vecs
    ]).tolist()

    for (index, _), transformed_vec in zip(valid_vecs, transformed_vecs):
        # UMAP은 샘플 수가 적을 때 요청 차원보다 낮은 차원만 만들 수 있다.
        # 저장/클러스터링 후속 로직이 고정 차원을 기대하므로 부족한 축은 0으로 채운다.
        reduced_vecs[index] = [
            *transformed_vec,
            *([0.0] * (n_components - len(transformed_vec))),
        ]

    return reduced_vecs


def reduce_for_clustering(vecs: list[list[float]]) -> list[list[float]]:
    valid_count = _valid_count(vecs)
    return reduce_dimension(
        vecs,
        # TODO: 고정 차원이 필요하면 UMAP_CLUSTER_COMPONENTS를 지정.
        n_components=_cluster_components(valid_count),
        min_dist=UMAP_CLUSTER_MIN_DIST,
        n_neighbors=UMAP_CLUSTER_NEIGHBORS,
    )


def reduce_for_view(vecs: list[list[float]]) -> list[list[float]]:
    return reduce_dimension(
        vecs,
        n_components=3,
        min_dist=1,
        n_neighbors=UMAP_VIEW_NEIGHBORS,
    )


def _fallback_dimensions(count: int, n_components: int) -> list[list[float]]:
    return [
        [float(index), *([0.0] * (n_components - 1))]
        for index in range(count)
    ]


def _is_zero_vector(vec: list[float]) -> bool:
    return not any(abs(value) > 1e-12 for value in vec)


def _valid_count(vecs: list[list[float]]) -> int:
    return sum(
        1
        for vec in vecs
        if not _is_zero_vector(vec)
    )


def _cluster_components(valid_count: int) -> int:
    if UMAP_CLUSTER_COMPONENTS > 0:
        return UMAP_CLUSTER_COMPONENTS

    if valid_count < 10:
        return 2

    if valid_count < 30:
        return 5

    if valid_count < 100:
        return 10

    if valid_count < 300:
        return 20

    return UMAP_CLUSTER_MAX_COMPONENTS
