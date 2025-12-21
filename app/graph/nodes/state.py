# /Users/shanzi/iemsProject/app/graph/nodes/state.py
from typing import TypedDict

class AgentState(TypedDict):
    team_home: str
    team_away: str

    recent_analysis: str
    history_analysis: str
    news_analysis: str

    odds_analysis: str
    strategy_analysis: str

    final_prediction: str