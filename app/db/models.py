"""
Database models for the NBA Prediction system.

Enhanced with execution metadata for prediction tracking and evaluation.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class PredictionRecord(Base):
    """Stores each prediction with full agent reports and evaluation data."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Match info
    team_home = Column(String, index=True)
    team_away = Column(String, index=True)

    # Individual agent reports
    recent_analysis = Column(Text)
    history_analysis = Column(Text)
    news_analysis = Column(Text)
    odds_analysis = Column(Text, nullable=True)
    strategy_analysis = Column(Text, nullable=True)

    # Final prediction
    final_result = Column(Text)

    # Execution metadata
    execution_time_seconds = Column(Float, nullable=True)
    agent_status = Column(JSON, nullable=True)  # {"agent_name": "success"|"failed"|"timeout"}

    # Evaluation (filled in after game is played)
    is_correct = Column(Boolean, default=None, nullable=True)
    actual_winner = Column(String, nullable=True)
    actual_score = Column(String, nullable=True)
    evaluated_at = Column(DateTime, nullable=True)
