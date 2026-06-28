from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from sqlalchemy import text
import logging

from contextlib import contextmanager

from config import(
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD
)

DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}"
    f"/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def db_connect():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            value = result.scalar()

            if value == 1:
                logging.info("Database connected successfully")

    except Exception as e:
        logging.exception(f"Database connection failed: {e}")
        raise SystemExit(1)