# /Users/shanzi/iemsProject/app/graph/nodes/final_predictor.py
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from app.core.config import llm
from app.graph.nodes.state import AgentState
import json

class GamePrediction(BaseModel):
    winner: str = Field(description="Full name of the predicted winning team")
    win_probability: float = Field(description="Win probability between 0 and 100")
    score_prediction: str = Field(description="Predicted score range, e.g., '110-105'")
    confidence_level: str = Field(description="Confidence level: High, Medium, Low")
    key_factors: list[str] = Field(description="3 key factors determining the outcome")
    risk_warning: str = Field(description="Biggest uncertainty factor (e.g., player absence)")
    summary: str = Field(description="Final comprehensive analysis summary, within 300 words")

def final_predictor_node(state: AgentState):
    """
    Agent 6: Final Decision Maker (Structured Output Version)
    """
    print("--- [Agent 6] Final Predictor is Synthesizing (Structured) ---")

    context = f"""
    [1. Recent Record]: {state.get('recent_analysis', 'None available')}
    [2. Historical Matchups]: {state.get('history_analysis', 'None available')}
    [3. News & Injuries]: {state.get('news_analysis', 'None available')}
    [4. Odds Market]: {state.get('odds_analysis', 'None available')}
    [5. Lineup Matchups]: {state.get('strategy_analysis', 'None available')}
    """

    home = state["team_home"]
    away = state["team_away"]

    structured_llm = llm.with_structured_output(GamePrediction)

    prompt = f"""
    You are the NBA Chief Decision System. Please make a final prediction for {home} vs {away} based on the reports from the following five experts.
    
    All expert reports are as follows:
    {context}
    
    Requirements:
    1. Even if expert opinions conflict (e.g., data favors A, odds favor B), you must make a unique choice.
    2. If the odds significantly contradict your prediction, explain this in the risk warning.
    3. Please provide a precise number for the win rate.
    """

    try:
        result: GamePrediction = structured_llm.invoke([HumanMessage(content=prompt)])
        return {"final_prediction": result.json()}
    except Exception as e:
        print(f"Structured output failed: {e}")
        fallback_result = {
            "winner": "Unknown", 
            "summary": f"Prediction failed due to parsing error: {str(e)}",
            "win_probability": 0
        }
        return {"final_prediction": json.dumps(fallback_result)}