# /Users/shanzi/iemsProject/app/db/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    team_home = Column(String)
    team_away = Column(String)

    recent_analysis = Column(Text)
    history_analysis = Column(Text)
    news_analysis = Column(Text)

    odds_analysis = Column(Text, nullable=True)
    strategy_analysis = Column(Text, nullable=True)

    final_result = Column(Text)

    is_correct = Column(Boolean, default=None, nullable=True)