from umap import UMAP

def reduce_dimension(vecs: list[list[float]]) -> list[list[float]]:
    reducer = UMAP(
        n_components=3,
        min_dist=0.1,
        metric="cosine",
        random_state=42,
    )

    return reducer.fit_transform(vecs).tolist()
