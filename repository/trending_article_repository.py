from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session


class TrendingArticleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_trending_article_job(
            self,
            job_id:int,
            status:str
    )-> bool:
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

    def get_trending_article_candidate(
            self,
            job_id:int
    )-> List[dict]:
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
        ), { job_id:job_id })

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    def update_trending_article_dimension(
            self,
            job_id: int,
            vectors: dict[int, list[float]],
    ) -> None:
        article_ids = list(vectors.keys())
        xs = [v[0] for v in vectors.values()]
        ys = [v[1] for v in vectors.values()]
        zs = [v[2] for v in vectors.values()]

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

