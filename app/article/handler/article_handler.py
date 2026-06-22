from app.messaging.KafkaConsumerManager import kafka_consumer_manager
from sqlalchemy import text
from app.article.repositories.article_repository import ArticleRepository
from app.article.repositories.post_vector_repo import PostVectorRepository
from app.db.database import SessionLocal
from app.models.bge_embedding import DenseEmbeddingModel

#파일 로딩 시점에 모델 인스턴스를 메모리에 딱 한 번만 단일 선언
embedding_model = DenseEmbeddingModel()

kafka_consumer_manager.register_handler("article-events", lambda event: handle_article_events(event))


def handle_article_events(event):
    db = SessionLocal()
    try:
        repo = ArticleRepository(db)
        vector_repo = PostVectorRepository(db)

        article_id = event.get("articleId")
        result = repo.get_article_by_id(event.get("articleId"))
        print(f"request article : {result}")

        if result and result.get("raw_text"):
            raw_text = result["raw_text"]

            vector_list = embedding_model.embed_text(raw_text).tolist()

            vector_repo.save_article_vector(article_id, vector_list)
        else:
            print(f"[Warning] No text found or article metadata is missing for ID: {article_id}")

    except Exception as e:
        print(f"[Handler Error] {e}")
    finally:
        db.close()