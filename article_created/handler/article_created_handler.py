import logging
from consumer.worker import handler
from article_created.service.article_embedding import embedding
from article_created.service.article_keword import extract_keywords_rank


@handler("article-created")
def article_created_handler(msg):
    title = msg.get("title")
    raw_text = msg.get("rawText")

    dense_vectors = embedding(title,raw_text)
    extract_keywords_rank(raw_text,dense_vectors,5)
    logging.info(msg)