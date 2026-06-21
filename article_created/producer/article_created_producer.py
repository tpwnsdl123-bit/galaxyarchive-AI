from confluent_kafka import Producer
import json

producer = Producer({
    "bootstrap.servers": "localhost:9092"
})

def publish_article_embedding(article_id:str, article_vecs:list[float],key_words:list[str]):
    payload = {
        "articleId":article_id,
        "vectors":article_vecs,
        "keywords":key_words
    }

    producer.produce(topic="article-embedding-complete",key=str(article_id),value=json.dumps(payload))