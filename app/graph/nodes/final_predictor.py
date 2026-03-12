"""
Agent 6: Final Decision Maker

Synthesizes reports from all 5 expert agents into a definitive
prediction with structured output and conflict resolution.
"""
import json
from langchain_core.messages import HumanMessage

from app.core.config import llm
from app.core.logger import get_logger, log_agent
from app.graph.nodes.state import AgentState
from app.graph.nodes.models import GamePrediction
from app.prompts.templates import FINAL_PREDICTOR_PROMPT

logger = get_logger("agent.final_predictor")


def _safe_get(state: dict, key: str) -> str:
    """Safely extract agent analysis, handling missing or failed agents."""
    value = state.get(key)
    if not value:
        return "[This agent did not produce a report — excluded from analysis]"
    return value


@log_agent("final_predictor")
def final_predictor_node(state: AgentState) -> dict:
    """
    Agent 6: Chief Decision System with structured prediction output.

    Aggregates all 5 expert reports with graceful handling of missing agents.
    Uses weighted decision-making: injuries > odds > recent form > tactics > history.
    """
    home = state["team_home"]
    away = state["team_away"]

    # Collect reports with graceful fallback for missing agents
    recent = _safe_get(state, "recent_analysis")
    history = _safe_get(state, "history_analysis")
    news = _safe_get(state, "news_analysis")
    odds = _safe_get(state, "odds_analysis")
    strategy = _safe_get(state, "strategy_analysis")

    # Log agent health status
    agent_status = state.get("agent_status", {})
    active_agents = sum(1 for v in agent_status.values() if v in ("success", "fallback"))
    logger.info(f"Synthesizing from {active_agents}/5 agent reports. Status: {agent_status}")

    prompt = FINAL_PREDICTOR_PROMPT.format(
        home_team=home,
        away_team=away,
        recent_analysis=recent,
        history_analysis=history,
        news_analysis=news,
        odds_analysis=odds,
        strategy_analysis=strategy,
    )

    structured_llm = llm.with_structured_output(GamePrediction)

    try:
        result: GamePrediction = structured_llm.invoke([HumanMessage(content=prompt)])
        return {"final_prediction": result.model_dump_json()}
    except Exception as e:
        logger.error(f"Structured output failed: {e}")
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            fallback_result = {
                "winner": "See summary",
                "win_probability": 0,
                "score_prediction": "N/A",
                "confidence_level": "Low",
                "key_factors": ["Prediction parsing failed — see summary"],
                "risk_warning": "Structured output failed, result may be less reliable",
                "agent_agreement": f"{active_agents}/5",
                "summary": response.content,
            }
            return {"final_prediction": json.dumps(fallback_result)}
        except Exception as e2:
            logger.error(f"Complete prediction failure: {e2}")
            error_result = {
                "winner": "Unknown",
                "win_probability": 0,
                "summary": f"Prediction failed: {str(e2)}",
            }
            return {"final_prediction": json.dumps(error_result)}
