import re
from itertools import combinations
from typing import TypedDict

import networkx as nx
from networkx.algorithms.community import louvain_communities
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

# 두 게시글 사이에 그래프 edge를 만들기 위한 기본 cosine 유사도 기준입니다.
# 값을 높일수록 더 엄격하고 잘게 나뉜 클러스터가 만들어집니다.
COMMUNITY_MIN_SIMILARITY = 0.65

# 게시글 1개짜리 커뮤니티는 실제 클러스터가 아니라 noise로 취급합니다.
COMMUNITY_MIN_CLUSTER_SIZE = 2

# 약한 edge들이 연쇄적으로 이어져 생기는 넓은 Louvain 커뮤니티를 걸러내는 기준입니다.
COMMUNITY_MIN_AVG_SIMILARITY = 0.62

# Louvain resolution은 클러스터 세분화 정도를 제어합니다.
# 값을 높일수록 커뮤니티를 더 적극적으로 쪼갭니다.
COMMUNITY_RESOLUTION = 1.8
COMMUNITY_RANDOM_SEED = 42

# 두 게시글이 명시적인 토픽 단어를 공유하면 더 낮은 임베딩 유사도에서도 edge를 허용합니다.
# 전체 기준을 낮춰 잡탕 클러스터를 늘리지 않고도 "Redis HA"와 "Redis SCAN" 같은 쌍을 보정합니다.
COMMUNITY_SHARED_TERM_MIN_SIMILARITY = 0.48
COMMUNITY_SHARED_TERM_BOOST = 0.14
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
    # 모든 게시글을 강제로 클러스터에 넣지 않고, 충분히 가까운 게시글 사이에만 그래프 edge를 만듭니다.
    normalized_dimensions = normalize([
        dimension
        for _, dimension in valid_dimensions
    ])
    similarities = cosine_similarity(normalized_dimensions)
    term_sets = _term_sets(terms_by_dimension, valid_dimensions)
    graph = _similarity_graph(len(valid_dimensions), similarities, term_sets)

    if graph.number_of_edges() == 0:
        return results

    # Louvain은 유사도 그래프에서 커뮤니티를 찾습니다.
    # 충분히 강한 edge가 없는 게시글은 고립 노드로 남기 때문에 noise로 유지됩니다.
    communities = louvain_communities(
        graph,
        weight="weight",
        resolution=COMMUNITY_RESOLUTION,
        seed=COMMUNITY_RANDOM_SEED,
    )

    cluster_id = 0
    for community in _sorted_communities(communities):
        if len(community) < COMMUNITY_MIN_CLUSTER_SIZE:
            continue

        community_indexes = sorted(community)
        # Louvain은 여러 약한 연결을 통해 너무 넓은 커뮤니티를 만들 수 있습니다.
        # 내부 평균 유사도가 낮은 커뮤니티는 신뢰하기 어려우므로 클러스터로 인정하지 않습니다.
        if _community_average_similarity(
            community_indexes,
            similarities,
            term_sets,
        ) < COMMUNITY_MIN_AVG_SIMILARITY:
            continue

        for local_index in community_indexes:
            original_index, _ = valid_dimensions[local_index]
            probability = _cluster_probability(
                local_index,
                community_indexes,
                similarities,
                term_sets,
            )
            results[original_index] = {
                "cluster_id": cluster_id,
                "probability": probability,
                "outlier_score": 1.0 - probability,
            }

        cluster_id += 1

    return results


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
        # 기본적으로는 임베딩 유사도를 우선합니다.
        # 다만 명시적인 토픽 단어를 공유하면 Redis 글처럼 경계선에 있는 쌍을 보정합니다.
        if similarity >= COMMUNITY_MIN_SIMILARITY or (
            shared_terms
            and similarity >= COMMUNITY_SHARED_TERM_MIN_SIMILARITY
        ):
            graph.add_edge(
                source,
                target,
                weight=_effective_similarity(source, target, similarities, term_sets),
            )

    return graph


def _term_sets(
    terms_by_dimension: list[list[str]] | None,
    valid_dimensions: list[tuple[int, list[float]]],
) -> list[set[str]]:
    if terms_by_dimension is None:
        return [set() for _ in valid_dimensions]

    return [
        _normalize_terms(terms_by_dimension[index])
        for index, _ in valid_dimensions
    ]


def _normalize_terms(terms: list[str]) -> set[str]:
    normalized_terms: set[str] = set()
    for term in terms:
        if not term:
            continue

        # 토픽 단어 매칭은 보수적으로 유지합니다.
        # ASCII 토큰만 사용해서 한국어 조사/일반 단어가 우연히 넓게 매칭되는 것을 피합니다.
        normalized_term = term.casefold()
        for token in re.split(r"[^0-9A-Za-z]+", normalized_term):
            if len(token) >= 2 and token not in COMMUNITY_STOPWORDS:
                normalized_terms.add(token)

    return normalized_terms


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
    # 클러스터 확률은 고정 1.0이 아니라, 해당 게시글이 커뮤니티 안의 다른 글들과
    # 평균적으로 얼마나 가까운지를 confidence로 사용합니다.
    neighbor_similarities = [
        _effective_similarity(local_index, other_index, similarities, term_sets)
        for other_index in community_indexes
        if other_index != local_index
    ]

    if not neighbor_similarities:
        return 0.0

    return max(0.0, min(1.0, sum(neighbor_similarities) / len(neighbor_similarities)))


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
