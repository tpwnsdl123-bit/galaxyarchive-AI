from sqlalchemy.orm import Session
from sqlalchemy import text

class ArticleKeywordRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_all(self, article_id:int, keywords)->None:
        sql = text("""
            INSERT INTO article_key_word_entity (article_id, keyword, similarity) VALUES (:article_id, :keyword, :similarity)    
        """)
        self.session.execute(sql, {"article_id": article_id, "keyword": keywords})



def save_article_keyword(session:Session, article_id:int, keywords)->None:
    sql = text("""
        INSERT INTO article_key_word_entity (article_id, keyword, similarity) VALUES (:article_id, :keyword, :similarity)
    """)

    for keyword in keywords:
        session.execute(sql, {"article_id": article_id, "keyword": keyword["keyword"], "similarity": keyword["score"]})
