"""
Agent State definition for the LangGraph workflow.

Uses TypedDict with Annotated reducers to support graceful degradation
and parallel agent fan-out/fan-in merging.
"""
from typing import TypedDict, Optional, Annotated


def merge_dicts(a: dict | None, b: dict | None) -> dict:
    """Reducer that merges agent_status dicts from parallel branches."""
    merged = dict(a) if a else {}
    if b:
        merged.update(b)
    return merged


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

    # Metadata for tracking agent health (merged from parallel agents)
    agent_status: Annotated[dict, merge_dicts]
