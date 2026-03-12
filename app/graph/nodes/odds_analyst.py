"""
Agent 4: Odds and Market Analyst

Analyzes betting odds and market sentiment using web search,
with caching and structured output.
"""
from langchain_core.messages import HumanMessage

from app.core.config import llm
from app.core.logger import get_logger, log_agent
from app.graph.nodes.state import AgentState
from app.graph.nodes.models import OddsAnalysis
from app.tools.nba_client import search_web
from app.prompts.templates import ODDS_ANALYST_PROMPT

logger = get_logger("agent.odds_analyst")


@log_agent("odds_analyst")
def odds_analyst_node(state: AgentState) -> dict:
    """
    Agent 4: Analyzes betting markets for sentiment and line movements.

    Pipeline: Web Search (cached) -> LLM Analysis -> Structured Output
    """
    home = state["team_home"]
    away = state["team_away"]

    query = f"{home} vs {away} odds prediction betting spread moneyline today"
    search_results = search_web(query, max_results=3)

    prompt = ODDS_ANALYST_PROMPT.format(
        home_team=home,
        away_team=away,
        search_results=search_results,
    )

    structured_llm = llm.with_structured_output(OddsAnalysis)

    try:
        result: OddsAnalysis = structured_llm.invoke([HumanMessage(content=prompt)])
        return {
            "odds_analysis": result.model_dump_json(),
            "agent_status": {"odds_analyst": "success"},
        }
    except Exception as e:
        logger.warning(f"Structured output failed, falling back to free text: {e}")
        response = llm.invoke([HumanMessage(content=prompt)])
        return {
            "odds_analysis": response.content,
            "agent_status": {"odds_analyst": "fallback"},
        }
