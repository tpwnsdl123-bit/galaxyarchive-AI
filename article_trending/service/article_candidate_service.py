from typing import List
from database.database import get_session
from repository.trending_article_repository import TrendingArticleRepository


def get_article_candidate(job_id:int)->List[tuple[int, list[float]]]|None:
    with get_session() as session:
        trending_repository = TrendingArticleRepository(session)
        is_valid = trending_repository.is_valid_job(job_id)
        if not is_valid:
            return None
        candidate_article_vector = trending_repository.get_trending_article_candidates(job_id)

        return candidate_article_vector
