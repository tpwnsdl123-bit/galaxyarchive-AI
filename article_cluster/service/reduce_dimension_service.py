from umap import UMAP
import logging


def reduce_dimension(vecs: list[list[float]])-> list[list[float]]:
    reducer = UMAP(n_components=3, min_dist=0.1, metric='cosine', random_state=42,)
    reduced_dimension = reducer.fit_transform(vecs)
    logging.info(reduced_dimension)
    return reduced_dimension