from sqlalchemy import text
from app.db.database import SessionLocal

def test_connection():
    db = SessionLocal()
    
    try:
        result = db.execute(text("SELECT 1"))
        print("DB connection successful:", result.scalar())

    except Exception as e:
        print("DB connection failed:", e)

    finally:
        db.close()