import logging

from consumer.worker import handler
from article_created.service.article_embedding import embedding
from article_created.service.article_keword import extract_keywords_rank
from producer.kafka_producer import kafka_publisher
from consumer.kafka_consumer import kafka_consumer


@handler("article-created")
def article_created_handler(msg):
    try:
        article_id = msg["articleId"]
        title = msg.get("title")
        raw_text = msg.get("rawText")

        dense_vectors = embedding(title,raw_text).tolist()
        keywords = extract_keywords_rank(raw_text,dense_vectors,5)

        message = {
            "articleId":article_id,
            "denseVectors":dense_vectors[0],
            "keywords":keywords
        }

        #임베딩 완료 메세지 발행
        kafka_publisher.publish_message(topic="embedding-created",message=message)

        #메세지 커밋처리
        kafka_consumer.commit()
    except Exception as e:
        #embedding fail dlq 발행
        logging.error(e)

        message={
            "articleId":msg["articleId"],
            "error":str(e)
        }
        kafka_publisher.publish_message(topic="embedding-created-dlq",message=message)

