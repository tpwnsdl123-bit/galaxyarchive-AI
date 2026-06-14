from app.messaging.KafakaConsumerManager import KafkaConsumerManager
from sqlalchemy import text
from app.article.repositories.article_repository import ArticleRepository
from app.db.database import SessionLocal

kafka_consumer_manager = KafkaConsumerManager()

kafka_consumer_manager.register_handler("article-events", lambda event: handle_article_events(event))


def handle_article_events(event):
    db = SessionLocal()
    repo = ArticleRepository(db)
    result = repo.get_article_by_id(event.get("articleId"))
    print(f"request article : {result}")