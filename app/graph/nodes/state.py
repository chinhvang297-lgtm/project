"""
Agent State definition for the LangGraph workflow.

Uses TypedDict with Optional types to support graceful degradation
when individual agents fail or timeout.
"""
from typing import TypedDict, Optional


class AgentState(TypedDict):
    """Shared state across all agents in the prediction workflow."""
    # Input
    team_home: str
    team_away: str

    # Agent outputs (Optional to support graceful degradation)
    recent_analysis: Optional[str]
    history_analysis: Optional[str]
    news_analysis: Optional[str]
    odds_analysis: Optional[str]
    strategy_analysis: Optional[str]

    # Final output
    final_prediction: Optional[str]

    # Metadata for tracking agent health
    agent_status: Optional[dict]  # {"agent_name": "success" | "failed" | "timeout"}
