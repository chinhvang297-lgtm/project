"""
Agent 1: Recent Performance Analyst

Analyzes the recent form and momentum of both teams using
real-time web search data with structured output.
"""
from langchain_core.messages import HumanMessage

from app.core.config import llm
from app.core.logger import get_logger, log_agent
from app.graph.nodes.state import AgentState
from app.graph.nodes.models import RecentAnalysis
from app.tools.nba_client import get_recent_games_stats
from app.prompts.templates import RECENT_ANALYST_PROMPT

logger = get_logger("agent.recent_analyst")


@log_agent("recent_analyst")
def recent_analyst_node(state: AgentState) -> dict:
    """
    Agent 1: Fetches recent game stats and produces structured analysis.

    Pipeline: Web Search -> LLM Analysis -> Structured Output
    """
    home_team = state["team_home"]
    away_team = state["team_away"]

    # Fetch data via web search (with retry & cache built into nba_client)
    home_stats = get_recent_games_stats(home_team, last_n=5)
    away_stats = get_recent_games_stats(away_team, last_n=5)

    prompt = RECENT_ANALYST_PROMPT.format(
        home_team=home_team,
        away_team=away_team,
        home_stats=home_stats,
        away_stats=away_stats,
    )

    # Structured output for consistent data quality
    structured_llm = llm.with_structured_output(RecentAnalysis)

    try:
        result: RecentAnalysis = structured_llm.invoke([HumanMessage(content=prompt)])
        return {
            "recent_analysis": result.model_dump_json(),
            "agent_status": {"recent_analyst": "success"},
        }
    except Exception as e:
        logger.warning(f"Structured output failed, falling back to free text: {e}")
        response = llm.invoke([HumanMessage(content=prompt)])
        return {
            "recent_analysis": response.content,
            "agent_status": {"recent_analyst": "fallback"},
        }
