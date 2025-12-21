# /Users/shanzi/iemsProject/app/api/routes.py
from fastapi import APIRouter, HTTPException
from app.graph.workflow import app_headless as graph_app
from app.db.session import SessionLocal
from app.db.models import PredictionRecord
from pydantic import BaseModel
import json

router = APIRouter()

class MatchRequest(BaseModel):
    team_home: str
    team_away: str

@router.post("/predict")
async def predict_match(request: MatchRequest):
    print(f"🚀 [Upgrade] API received the request: {request.team_home} vs {request.team_away}")
    
    initial_state = {
        "team_home": request.team_home,
        "team_away": request.team_away
    }
    
    try:
        output = graph_app.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    final_json_str = output.get("final_prediction", "{}")
    try:
        final_data = json.loads(final_json_str)
    except:
        final_data = {"summary": final_json_str} 

    db = SessionLocal()
    record = PredictionRecord(
        team_home=request.team_home,
        team_away=request.team_away,
        recent_analysis=output.get("recent_analysis"),
        history_analysis=output.get("history_analysis"),
        news_analysis=output.get("news_analysis"),
        odds_analysis=output.get("odds_analysis"),
        strategy_analysis=output.get("strategy_analysis"),
        final_result=final_json_str 
    )
    db.add(record)
    db.commit()
    db.close()
    
    return {
        "matchup": f"{request.team_home} vs {request.team_away}",
        "prediction_details": final_data 
    }