from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Читаємо URL БД з env; працює і в Docker, і локально.
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://vitacode:vc_pass@127.0.0.1:3306/vitacode"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
