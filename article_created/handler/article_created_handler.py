import logging

from consumer.worker import handler
from article_created.service.article_embedding import embedding
from article_created.service.article_keword import extract_keywords_rank
from producer.kafka_producer import kafka_publisher
from consumer.kafka_consumer import kafka_consumer

from article_created.service.persist_embedding_service import article_embedding_persist
from article_created.service.article_service import validate_article


@handler("article-created")
def article_created_handler(msg):
    article_id:int = msg.get("articleId")

    if article_id is None:
        logging.exception("article id is undefined")
        kafka_consumer.commit()
        return

    try:
        logging.info(f"{article_id} : start embedding task")
        title = msg.get("title")
        raw_text = msg.get("rawText")

        #임베딩은 연산 자원 소모가 많기 때문에 유효하지 않은 요청 체크 후 게시글이 유효한지 확인하고 임베딩 진행
        exist_article = validate_article(article_id)

        if not exist_article:
            raise ValueError("invalid article id")

        #Dense 임베딩
        dense_vectors = embedding(title,raw_text).tolist()
        #키워드 추출
        keywords = extract_keywords_rank(raw_text,dense_vectors,5)

        article_embedding_persist(article_id,dense_vectors[0],keywords)

        message = { "articleId":article_id, "status":"COMPLETED" }

        #임베딩 완료 메세지 발행
        kafka_publisher.publish_message(topic="embedding-complete",message=message)

        #메세지 커밋처리
        kafka_consumer.commit()
    except Exception as e:

        #embedding fail 메세지 발행
        logging.error(e)

        message = {"articleId": article_id, "status": "FAIL", "error": str(e)}

        kafka_publisher.publish_message(topic="embedding-complete",message=message)
        #발행 후 commit 처리
        kafka_consumer.commit()

