from umap import UMAP
import math

def reduce_dimension(
    vecs: list[list[float]],
    n_components: int,
    min_dist: float,
) -> list[list[float]]:
    if len(vecs) < 3:
        return _fallback_dimensions(len(vecs), n_components)

    reducer = UMAP(
        n_components=n_components,
        n_neighbors=max(2, min(15, len(vecs) - 1)),
        min_dist=min_dist,
        metric="cosine",
        init="random",
        n_jobs=1,
        random_state=42,
    )

    return reducer.fit_transform(vecs).tolist()


def reduce_for_clustering(vecs: list[list[float]]) -> list[list[float]]:
    count = len(vecs)

    return reduce_dimension(
        vecs,
        n_components=min(
            15,
            max(2, int(math.sqrt(count))),
            count - 2,
        ),
        min_dist=0,
    )


def reduce_for_view(vecs: list[list[float]]) -> list[list[float]]:
    return reduce_dimension(
        vecs,
        n_components=3,
        min_dist=1,
    )


def _fallback_dimensions(count: int, n_components: int) -> list[list[float]]:
    return [
        [float(index), *([0.0] * (n_components - 1))]
        for index in range(count)
    ]
