import re
from itertools import combinations
from typing import TypedDict

import igraph as ig
import leidenalg
import networkx as nx
from networkx.algorithms.community import louvain_communities
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

# 클러스터 탐지 알고리즘입니다. 기본값은 Louvain보다 커뮤니티 연결성이 안정적인 Leiden입니다.
COMMUNITY_ALGORITHM = "leiden"

# 공통 토픽 단어가 없는 두 게시글 사이에 edge를 만들기 위한 cosine 유사도 기준입니다.
COMMUNITY_MIN_SIMILARITY = 0.82

# 이 개수보다 작은 커뮤니티는 실제 클러스터가 아니라 noise로 취급합니다.
COMMUNITY_MIN_CLUSTER_SIZE = 2

# 약한 edge가 연쇄적으로 이어져 생기는 넓은 커뮤니티를 걸러내는 내부 평균 유사도 하한입니다.
COMMUNITY_MIN_AVG_SIMILARITY = 0.72

# Leiden/Louvain의 클러스터 세분화 정도입니다. 제목 토픽 edge를 이미 보수적으로 만들기 때문에 기본값에 가깝게 둡니다.
COMMUNITY_RESOLUTION = 1.0

# 같은 입력에서 같은 클러스터 결과를 얻기 위한 난수 seed입니다.
COMMUNITY_RANDOM_SEED = 42

# 토픽 단어를 공유하는 게시글끼리는 이 유사도 이상이면 edge를 허용합니다.
COMMUNITY_SHARED_TERM_MIN_SIMILARITY = 0.35

# 토픽 단어를 공유할 때 cosine 유사도에 더하는 보정값입니다.
COMMUNITY_SHARED_TERM_BOOST = 0.20

# 게시글을 클러스터 소속으로 인정하기 위한 최소 confidence입니다.
COMMUNITY_MIN_PROBABILITY = 0.65

# 토픽 단어 매칭에서 제외할 일반적인 불용어입니다.
COMMUNITY_STOPWORDS = {
    "and",
    "for",
    "the",
    "with",
}


class ClusterResult(TypedDict):
    cluster_id: int
    probability: float
    outlier_score: float


def cluster_dimensions(
    dimensions: list[list[float]],
    terms_by_dimension: list[list[str]] | None = None,
) -> list[ClusterResult]:
    if not dimensions:
        return []

    results = [_noise_result() for _ in dimensions]
    valid_dimensions = [
        (index, dimension)
        for index, dimension in enumerate(dimensions)
        if not _is_zero_vector(dimension)
    ]

    if len(valid_dimensions) < COMMUNITY_MIN_CLUSTER_SIZE:
        return results

    # 임베딩은 cosine 유사도로 비교하므로 먼저 정규화합니다.
    # 모든 게시글을 강제로 묶지 않고, 충분히 가까운 게시글 사이에만 그래프 edge를 만듭니다.
    normalized_dimensions = normalize([
        dimension
        for _, dimension in valid_dimensions
    ])
    similarities = cosine_similarity(normalized_dimensions)
    term_sets = _term_sets(terms_by_dimension, valid_dimensions)
    graph = _similarity_graph(len(valid_dimensions), similarities, term_sets)

    if graph.number_of_edges() == 0:
        return results

    # Leiden/Louvain은 유사도 그래프에서 커뮤니티를 찾습니다.
    # 충분히 강한 edge가 없는 게시글은 고립 노드로 남기 때문에 noise로 유지됩니다.
    communities = _detect_communities(graph)

    cluster_id = 0
    for community in _sorted_communities(communities):
        if len(community) < COMMUNITY_MIN_CLUSTER_SIZE:
            continue

        community_indexes = sorted(community)
        # 그래프 기반 알고리즘은 약한 연결을 통해 너무 넓은 커뮤니티를 만들 수 있습니다.
        # 내부 평균 유사도가 낮은 커뮤니티는 하나의 주제로 보기 어려워 클러스터로 인정하지 않습니다.
        if _community_average_similarity(
            community_indexes,
            similarities,
            term_sets,
        ) < COMMUNITY_MIN_AVG_SIMILARITY:
            continue

        candidates: list[tuple[int, float]] = []
        for local_index in community_indexes:
            original_index, _ = valid_dimensions[local_index]
            probability = _cluster_probability(
                local_index,
                community_indexes,
                similarities,
                term_sets,
            )
            if probability >= COMMUNITY_MIN_PROBABILITY:
                candidates.append((original_index, probability))

        if len(candidates) < COMMUNITY_MIN_CLUSTER_SIZE:
            continue

        for original_index, probability in candidates:
            results[original_index] = {
                "cluster_id": cluster_id,
                "probability": probability,
                "outlier_score": 1.0 - probability,
            }

        cluster_id += 1

    return results


def _detect_communities(graph: nx.Graph) -> list[set[int]]:
    if COMMUNITY_ALGORITHM == "leiden":
        return _leiden_communities(graph)

    if COMMUNITY_ALGORITHM == "louvain":
        return list(louvain_communities(
            graph,
            weight="weight",
            resolution=COMMUNITY_RESOLUTION,
            seed=COMMUNITY_RANDOM_SEED,
        ))

    raise ValueError(
        f"Unsupported COMMUNITY_ALGORITHM: {COMMUNITY_ALGORITHM}. "
        "Use 'leiden' or 'louvain'."
    )


def _leiden_communities(graph: nx.Graph) -> list[set[int]]:
    edges = list(graph.edges(data=True))
    igraph = ig.Graph(
        n=graph.number_of_nodes(),
        edges=[(source, target) for source, target, _ in edges],
        directed=False,
    )
    weights = [
        float(edge_data.get("weight", 1.0))
        for _, _, edge_data in edges
    ]

    partition = leidenalg.find_partition(
        igraph,
        leidenalg.RBConfigurationVertexPartition,
        weights=weights,
        resolution_parameter=COMMUNITY_RESOLUTION,
        seed=COMMUNITY_RANDOM_SEED,
    )
    return [
        set(community)
        for community in partition
    ]


def _similarity_graph(
    count: int,
    similarities,
    term_sets: list[set[str]],
) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(count))

    for source, target in combinations(range(count), 2):
        similarity = float(similarities[source][target])
        shared_terms = term_sets[source] & term_sets[target]
        # 공통 토픽 단어가 있으면 같은 주제일 가능성이 높아 낮은 기준을 씁니다.
        # 공통 토픽 단어가 없으면 넓은 의미만 비슷한 글이 섞이지 않도록 높은 기준을 씁니다.
        if _should_connect(similarity, shared_terms):
            graph.add_edge(
                source,
                target,
                weight=_effective_similarity(source, target, similarities, term_sets),
            )

    return graph


def _should_connect(similarity: float, shared_terms: set[str]) -> bool:
    if shared_terms:
        return similarity >= COMMUNITY_SHARED_TERM_MIN_SIMILARITY

    return similarity >= COMMUNITY_MIN_SIMILARITY


def _term_sets(
    terms_by_dimension: list[list[str]] | None,
    valid_dimensions: list[tuple[int, list[float]]],
) -> list[set[str]]:
    if terms_by_dimension is None:
        return [set() for _ in valid_dimensions]

    return [
        # 키워드 추출 결과는 "kafka", "db" 같은 넓은 단어가 자주 섞입니다.
        # 클러스터 연결 보정에는 제목 토큰만 사용해서 느슨한 주제 연결을 줄입니다.
        _normalize_terms(terms_by_dimension[index][:1])
        for index, _ in valid_dimensions
    ]


def _normalize_terms(terms: list[str]) -> set[str]:
    normalized_terms: set[str] = set()
    for term in terms:
        if not term:
            continue

        # 토픽 단어 매칭은 보수적으로 처리합니다.
        # 제목에서 나온 영문/숫자/한글 토큰만 사용해 추출 키워드의 넓은 단어가 edge를 만들지 않게 합니다.
        normalized_term = term.casefold()
        for token in re.split(r"[^0-9A-Za-z가-힣]+", normalized_term):
            token = _normalize_token(token)
            if len(token) >= 2 and token not in COMMUNITY_STOPWORDS:
                normalized_terms.add(token)

    return normalized_terms


def _normalize_token(token: str) -> str:
    match = re.match(r"^([0-9a-z]+)[가-힣]+$", token)
    if match:
        return match.group(1)

    return token


def _term_boost(shared_terms: set[str]) -> float:
    if not shared_terms:
        return 0.0

    return COMMUNITY_SHARED_TERM_BOOST


def _sorted_communities(communities: list[set[int]]) -> list[set[int]]:
    return sorted(
        communities,
        key=lambda community: min(community),
    )


def _cluster_probability(
    local_index: int,
    community_indexes: list[int],
    similarities,
    term_sets: list[set[str]],
) -> float:
    # 클러스터 확률은 고정 1.0이 아니라, 같은 커뮤니티 안의 다른 글들과
    # 평균적으로 얼마나 가까운지를 confidence로 사용합니다.
    neighbor_similarities = [
        _effective_similarity(local_index, other_index, similarities, term_sets)
        for other_index in community_indexes
        if other_index != local_index
    ]

    if not neighbor_similarities:
        return 0.0

    confidence = sum(neighbor_similarities) / len(neighbor_similarities)
    return max(0.0, min(1.0, confidence))


def _community_average_similarity(
    community_indexes: list[int],
    similarities,
    term_sets: list[set[str]],
) -> float:
    pair_similarities = [
        _effective_similarity(source, target, similarities, term_sets)
        for source, target in combinations(community_indexes, 2)
    ]

    if not pair_similarities:
        return 0.0

    return sum(pair_similarities) / len(pair_similarities)


def _effective_similarity(
    source: int,
    target: int,
    similarities,
    term_sets: list[set[str]],
) -> float:
    shared_terms = term_sets[source] & term_sets[target]
    return min(1.0, float(similarities[source][target]) + _term_boost(shared_terms))


def _noise_result() -> ClusterResult:
    return {
        "cluster_id": -1,
        "probability": 0.0,
        "outlier_score": 1.0,
    }


def _is_zero_vector(dimension: list[float]) -> bool:
    return not any(abs(value) > 1e-12 for value in dimension)
