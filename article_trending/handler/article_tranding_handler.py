import logging

from article_trending.service.trending_article_dimension_service import get_article_dimension
from consumer.kafka_consumer import kafka_consumer
from consumer.worker import handler
from database.database import get_session
from repository.trending_article_repository import TrendingArticleRepository


@handler("article-tranding-calculated")
def article_trending_calculated_handler(msg)->None:
    # Spring에서 발행한 TrendingArticleCalculateEvent의 jobId를 꺼낸다.
    job_id = _extract_job_id(msg)
    # traceId는 처리 추적용 값이라 로깅에만 사용한다.
    trace_id = msg.get("traceId") if isinstance(msg, dict) else None

    if job_id is None:
        logging.warning("trending article job id is undefined: %s", msg)
        kafka_consumer.commit()
        return

    try:
        logging.info("%s : start trending article dimension task traceId=%s", job_id, trace_id)

        with get_session() as session:
            trending_repository = TrendingArticleRepository(session)
            # 이미 처리 중이거나 완료된 job은 중복 계산하지 않는다.
            if not trending_repository.is_valid_job(job_id, "PENDING"):
                logging.warning("%s : trending article job is not pending traceId=%s", job_id, trace_id)
                kafka_consumer.commit()
                return

            # 계산 시작을 DB에 먼저 반영한다.
            trending_repository.update_trending_job_status(job_id, "RUNNING")

        with get_session() as session:
            trending_repository = TrendingArticleRepository(session)
            # job에 포함된 인기글의 원본 임베딩 벡터를 가져온다.
            candidate_vecs = trending_repository.get_trending_article_candidates(job_id)
            # 임베딩 벡터를 화면 배치용 3차원 좌표로 줄인다.
            article_dimensions = get_article_dimension(candidate_vecs)

            # 계산된 x, y, z를 trending_article에 저장하고 job을 완료 처리한다.
            trending_repository.update_trending_article_dimension(job_id, article_dimensions)
            trending_repository.update_trending_job_status(job_id, "DONE")

        kafka_consumer.commit()
        logging.info("%s : finish trending article dimension task traceId=%s", job_id, trace_id)

    except Exception as e:
        logging.error("%s : failed trending article dimension task traceId=%s error=%s", job_id, trace_id, e, exc_info=True)

        # 실패 상태도 DB에 남겨 Spring 쪽에서 후속 처리를 할 수 있게 한다.
        with get_session() as session:
            TrendingArticleRepository(session).update_trending_job_status(job_id, "FAILED")

        kafka_consumer.commit()


def _extract_job_id(msg) -> int | None:
    # Kafka payload는 JSON object(dict)여야 한다.
    if not isinstance(msg, dict):
        return None

    job_id = msg.get("jobId")
    if job_id is None:
        return None

    try:
        # Kotlin Long 값이 JSON 숫자나 문자열로 와도 int로 통일한다.
        return int(job_id)
    except (TypeError, ValueError):
        return None
