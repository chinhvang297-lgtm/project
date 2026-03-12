"""
Agent 2: Historical Matchup Analyst

Searches for historical matchup data via web search and produces
tactical analysis with structured output.
"""
from langchain_core.messages import HumanMessage

from app.core.config import llm
from app.core.logger import get_logger, log_agent
from app.graph.nodes.state import AgentState
from app.graph.nodes.models import HistoryAnalysis
from app.tools.nba_client import search_web
from app.prompts.templates import HISTORY_ANALYST_PROMPT

logger = get_logger("agent.history_analyst")


@log_agent("history_analyst")
def history_analyst_node(state: AgentState) -> dict:
    """
    Agent 2: Historical analysis via web search.

    Pipeline: Web Search -> LLM Analysis -> Structured Output
    """
    home_team = state["team_home"]
    away_team = state["team_away"]

    search_query = f"{home_team} vs {away_team} head to head history record all time series"

    # Search web for historical matchup data
    historical_context = search_web(search_query, max_results=3)

    prompt = HISTORY_ANALYST_PROMPT.format(
        home_team=home_team,
        away_team=away_team,
        historical_context=historical_context,
    )

    structured_llm = llm.with_structured_output(HistoryAnalysis)

    try:
        result: HistoryAnalysis = structured_llm.invoke([HumanMessage(content=prompt)])
        return {
            "history_analysis": result.model_dump_json(),
            "agent_status": {"history_analyst": "success"},
        }
    except Exception as e:
        logger.warning(f"Structured output failed, falling back to free text: {e}")
        response = llm.invoke([HumanMessage(content=prompt)])
        return {
            "history_analysis": response.content,
            "agent_status": {"history_analyst": "fallback"},
        }
