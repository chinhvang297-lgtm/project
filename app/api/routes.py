"""
API routes for the NBA Prediction system.

Endpoints:
- POST /predict          - Run a full prediction for a matchup
- GET  /predictions      - List prediction history with pagination
- GET  /predictions/{id} - Get a specific prediction by ID
- POST /evaluate/{id}    - Submit actual game result for evaluation
- GET  /stats            - Get prediction accuracy statistics
- GET  /health           - Health check endpoint
"""
import time
import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from app.graph.workflow import app_workflow
from app.db.session import get_db
from app.db.models import PredictionRecord
from app.core.logger import get_logger
from app.core.cache import prediction_cache, TTLCache

logger = get_logger("api")

router = APIRouter()


# ─── Request/Response Models ─────────────────────────────────────────────────

class MatchRequest(BaseModel):
    team_home: str
    team_away: str


class EvaluationRequest(BaseModel):
    actual_winner: str
    actual_score: Optional[str] = None


# ─── POST /predict ────────────────────────────────────────────────────────────

@router.post("/predict")
async def predict_match(request: MatchRequest, db: Session = Depends(get_db)):
    """
    Run a full multi-agent prediction for an NBA matchup.

    The prediction pipeline:
    1. Check cache for recent predictions of the same matchup
    2. Run 5 parallel analyst agents (with timeout + graceful degradation)
    3. Synthesize via the final predictor agent
    4. Store result in database
    5. Return structured prediction
    """
    logger.info(f"Prediction request: {request.team_home} vs {request.team_away}")

    # Check cache for recent prediction of same matchup
    cache_key = TTLCache._make_key("prediction", request.team_home, request.team_away)
    cached = prediction_cache.get(cache_key)
    if cached:
        logger.info("Returning cached prediction")
        return cached

    initial_state = {
        "team_home": request.team_home,
        "team_away": request.team_away,
    }

    start_time = time.time()
    try:
        output = app_workflow.invoke(initial_state)
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction pipeline failed: {str(e)}")

    execution_time = time.time() - start_time
    logger.info(f"Prediction completed in {execution_time:.2f}s")

    # Parse final prediction
    final_json_str = output.get("final_prediction", "{}")
    try:
        final_data = json.loads(final_json_str)
    except (json.JSONDecodeError, TypeError):
        final_data = {"summary": str(final_json_str)}

    # Store in database with execution metadata
    record = PredictionRecord(
        team_home=request.team_home,
        team_away=request.team_away,
        recent_analysis=output.get("recent_analysis"),
        history_analysis=output.get("history_analysis"),
        news_analysis=output.get("news_analysis"),
        odds_analysis=output.get("odds_analysis"),
        strategy_analysis=output.get("strategy_analysis"),
        final_result=final_json_str,
        execution_time_seconds=round(execution_time, 2),
        agent_status=output.get("agent_status"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    response = {
        "id": record.id,
        "matchup": f"{request.team_home} vs {request.team_away}",
        "prediction_details": final_data,
        "execution_time_seconds": round(execution_time, 2),
        "agent_status": output.get("agent_status", {}),
    }

    # Cache the result
    prediction_cache.set(cache_key, response)

    return response


# ─── GET /predictions ─────────────────────────────────────────────────────────

@router.get("/predictions")
async def list_predictions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    team: Optional[str] = Query(None, description="Filter by team name"),
    db: Session = Depends(get_db),
):
    """
    List prediction history with pagination and optional team filter.

    Enables tracking of prediction patterns over time.
    """
    query = db.query(PredictionRecord).order_by(desc(PredictionRecord.created_at))

    if team:
        query = query.filter(
            (PredictionRecord.team_home.contains(team))
            | (PredictionRecord.team_away.contains(team))
        )

    total = query.count()
    records = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "predictions": [
            {
                "id": r.id,
                "matchup": f"{r.team_home} vs {r.team_away}",
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "winner": _extract_winner(r.final_result),
                "is_correct": r.is_correct,
                "execution_time": r.execution_time_seconds,
            }
            for r in records
        ],
    }


# ─── GET /predictions/{id} ───────────────────────────────────────────────────

@router.get("/predictions/{prediction_id}")
async def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Get detailed prediction by ID, including all agent reports."""
    record = db.query(PredictionRecord).filter(PredictionRecord.id == prediction_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return {
        "id": record.id,
        "matchup": f"{record.team_home} vs {record.team_away}",
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "agent_reports": {
            "recent_analysis": _safe_json_parse(record.recent_analysis),
            "history_analysis": _safe_json_parse(record.history_analysis),
            "news_analysis": _safe_json_parse(record.news_analysis),
            "odds_analysis": _safe_json_parse(record.odds_analysis),
            "strategy_analysis": _safe_json_parse(record.strategy_analysis),
        },
        "final_prediction": _safe_json_parse(record.final_result),
        "execution_metadata": {
            "execution_time_seconds": record.execution_time_seconds,
            "agent_status": record.agent_status,
        },
        "evaluation": {
            "is_correct": record.is_correct,
            "actual_winner": record.actual_winner,
            "actual_score": record.actual_score,
            "evaluated_at": record.evaluated_at.isoformat() if record.evaluated_at else None,
        },
    }


# ─── POST /evaluate/{id} ─────────────────────────────────────────────────────

@router.post("/evaluate/{prediction_id}")
async def evaluate_prediction(
    prediction_id: int,
    evaluation: EvaluationRequest,
    db: Session = Depends(get_db),
):
    """
    Submit actual game result to evaluate a prediction.

    This closes the feedback loop — enabling accuracy tracking
    and continuous improvement of the prediction system.
    """
    record = db.query(PredictionRecord).filter(PredictionRecord.id == prediction_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Prediction not found")

    if record.is_correct is not None:
        raise HTTPException(status_code=400, detail="Prediction already evaluated")

    # Compare predicted winner with actual winner
    predicted_winner = _extract_winner(record.final_result)
    is_correct = (
        predicted_winner.lower().strip() == evaluation.actual_winner.lower().strip()
        if predicted_winner
        else None
    )

    record.actual_winner = evaluation.actual_winner
    record.actual_score = evaluation.actual_score
    record.is_correct = is_correct
    record.evaluated_at = datetime.utcnow()
    db.commit()

    logger.info(
        f"Evaluation: prediction #{prediction_id} "
        f"predicted={predicted_winner}, actual={evaluation.actual_winner}, "
        f"correct={is_correct}"
    )

    return {
        "prediction_id": prediction_id,
        "predicted_winner": predicted_winner,
        "actual_winner": evaluation.actual_winner,
        "is_correct": is_correct,
        "message": "Evaluation recorded successfully",
    }


# ─── GET /stats ───────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_prediction_stats(db: Session = Depends(get_db)):
    """
    Get prediction accuracy statistics.

    Provides a dashboard of system performance for continuous evaluation.
    """
    total = db.query(func.count(PredictionRecord.id)).scalar()
    evaluated = db.query(func.count(PredictionRecord.id)).filter(
        PredictionRecord.is_correct.isnot(None)
    ).scalar()
    correct = db.query(func.count(PredictionRecord.id)).filter(
        PredictionRecord.is_correct == True  # noqa: E712
    ).scalar()
    avg_time = db.query(func.avg(PredictionRecord.execution_time_seconds)).scalar()

    return {
        "total_predictions": total,
        "evaluated": evaluated,
        "correct": correct,
        "accuracy": round(correct / evaluated * 100, 1) if evaluated > 0 else None,
        "accuracy_label": f"{correct}/{evaluated}" if evaluated > 0 else "No evaluations yet",
        "avg_execution_time_seconds": round(avg_time, 2) if avg_time else None,
    }


# ─── GET /health ──────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "NBA Prediction Agent System",
        "cache_size": prediction_cache.size,
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _safe_json_parse(text: Optional[str]):
    """Parse JSON string, returning the raw text if parsing fails."""
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def _extract_winner(final_result: Optional[str]) -> Optional[str]:
    """Extract the predicted winner from the final result JSON."""
    if not final_result:
        return None
    try:
        data = json.loads(final_result)
        return data.get("winner")
    except (json.JSONDecodeError, TypeError):
        return None
