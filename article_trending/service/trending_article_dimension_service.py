from typing import List

import numpy as np
from umap import UMAP


def get_article_dimension(
    candidate_vecs: List[tuple[int, list[float]]],
    article_id: int | None = None,
) -> list[tuple[int, list[float]]]:
    """
    인기글 임베딩 벡터를 3차원 좌표로 변환한다.

    candidate_vecs: [(article_id, vector), ...]
    article_id: 이 게시글을 (0, 0, 0) 기준점으로 이동한다. 없으면 이동하지 않는다.
    return: [(article_id, [x, y, z]), ...]
    """
    if not candidate_vecs:
        return []

    # 이후 결과를 원래 게시글과 다시 묶기 위해 article_id 순서를 따로 보관한다.
    article_ids = [item[0] for item in candidate_vecs]

    if len(candidate_vecs) <= 4:
        # 데이터가 너무 적으면 UMAP 이웃 그래프가 불안정하므로 고정 좌표를 사용한다.
        dimensions = _get_tiny_sample_dimensions(len(candidate_vecs))
    else:
        # UMAP 입력은 2차원 배열이어야 한다. shape: (게시글 수, 임베딩 차원)
        vectors = np.asarray(
            [vector for _, vector in candidate_vecs],
            dtype=np.float32,
        )
        dimensions = _reduce_to_3d(vectors)

    # 기준 article_id가 있으면 해당 게시글이 (0, 0, 0)에 오도록 전체 좌표를 평행 이동한다.
    dimensions = _move_origin_to_article(article_ids, dimensions, article_id)

    # 저장 레이어가 쓰기 쉬운 [(article_id, [x, y, z]), ...] 형태로 반환한다.
    return [
        (current_article_id, dimension.astype(float).tolist())
        for current_article_id, dimension in zip(article_ids, dimensions)
    ]


def _reduce_to_3d(vectors: np.ndarray) -> np.ndarray:
    # cosine metric은 임베딩 벡터의 방향 유사도를 기준으로 가까운 글을 배치하기 위한 설정이다.
    reducer = UMAP(
        n_components=3,
        metric="cosine",
        n_neighbors=min(15, len(vectors) - 1),
        min_dist=0.1,
        random_state=42,
    )

    return reducer.fit_transform(vectors)


def _move_origin_to_article(
    article_ids: list[int],
    dimensions: np.ndarray,
    article_id: int | None,
) -> np.ndarray:
    if article_id is None:
        return dimensions

    if article_id not in article_ids:
        return dimensions

    # 기준 게시글 좌표를 모든 좌표에서 빼면 기준 게시글은 원점이 되고 상대 위치는 유지된다.
    origin_index = article_ids.index(article_id)
    return dimensions - dimensions[origin_index]


def _get_tiny_sample_dimensions(article_count: int) -> np.ndarray:
    # 1~4개짜리 입력은 시각화에서 겹치지 않도록 단순한 고정 좌표를 부여한다.
    dimensions_by_count = {
        1: [[0.0, 0.0, 0.0]],
        2: [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
        3: [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        4: [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0, 0.0]],
    }

    return np.asarray(dimensions_by_count[article_count], dtype=np.float32)
