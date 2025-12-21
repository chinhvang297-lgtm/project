# /Users/shanzi/iemsProject/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./nba_prediction.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully (SQLite)")
    except Exception as e:
        print(f"Database initialization failed: {e}")