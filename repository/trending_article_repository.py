import json
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session


class TrendingArticleRepository:
    def __init__(self, session: Session):
        self.session = session

    def is_valid_job(
            self,
            job_id:int,
            status:str = "PENDING"
    )-> bool:
        # 요청받은 job이 기대 상태인지 확인한다. 기본값은 아직 처리 전인 PENDING이다.
        result = self.session.execute(text(
            """
            SELECT EXISTS(
                SELECT 1
                FROM trending_article_job
                WHERE id = :job_id
                AND status = :status
            )
            """
        ),{"job_id":job_id, "status":status})

        return bool(result.scalar())

    def update_trending_job_status(
            self,
            job_id: int,
            status: str,
    ) -> None:
        # Spring 도메인의 TrendingJobStatus 값(PENDING/RUNNING/DONE/FAILED)을 그대로 저장한다.
        self.session.execute(text(
            """
            UPDATE trending_article_job
            SET status = :status
            WHERE id = :job_id
            """
        ), {"job_id": job_id, "status": status})

    def get_trending_article_candidates(
            self,
            job_id:int
    )-> List[tuple[int, list[float]]]:
        # 해당 job에 묶인 인기글과 각 글의 임베딩 벡터를 조회한다.
        result = self.session.execute(text(
            """
            SELECT
                a.id AS article_id,
                v.vector AS vector
            FROM article a
            JOIN trending_article t ON a.id = t.article_id
            JOIN article_vector v ON v.article_id = a.id
            WHERE t.trending_article_job_id = :job_id
            AND a.is_deleted = false
            """
        ), {"job_id": job_id})

        # UMAP 서비스 입력 형태인 [(article_id, vector), ...]로 맞춘다.
        return [
            (row["article_id"], _json_or_value(row["vector"]))
            for row in result.mappings().all()
        ]

    def update_trending_article_dimension(
            self,
            job_id: int,
            vectors: List[tuple[int, list[float]]],
    ) -> None:
        # 저장할 좌표가 없으면 UPDATE를 실행하지 않는다.
        if not vectors:
            return

        # PostgreSQL unnest로 한 번에 여러 article의 x/y/z를 업데이트하기 위해 컬럼별 배열로 나눈다.
        article_ids = [article_id for article_id, _ in vectors]
        xs = [vector[0] for _, vector in vectors]
        ys = [vector[1] for _, vector in vectors]
        zs = [vector[2] for _, vector in vectors]

        self.session.execute(
            text(
                """
                UPDATE trending_article AS t
                SET x = v.x,
                    y = v.y,
                    z = v.z
                FROM (SELECT *
                      FROM unnest(
                              CAST(:article_ids AS bigint[]),
                              CAST(:xs AS double precision[]),
                              CAST(:ys AS double precision[]),
                              CAST(:zs AS double precision[])
                           )) AS v(article_id, x, y, z)
                WHERE t.trending_article_job_id = :job_id
                  AND t.article_id = v.article_id
                """
            ),
            {
                "job_id": job_id,
                "article_ids": article_ids,
                "xs": xs,
                "ys": ys,
                "zs": zs,
            },
        )


def _json_or_value(value):
    # DB 드라이버가 vector 컬럼을 JSON 문자열로 반환하는 경우 list로 변환한다.
    if isinstance(value, str):
        return json.loads(value)

    return value

