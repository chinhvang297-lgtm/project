"""
Agent 5: Strategy and Matchup Coach

Analyzes tactical matchups, starting lineups, and bench depth
with structured output for consistent analysis quality.
"""
from langchain_core.messages import HumanMessage

from app.core.config import llm
from app.core.logger import get_logger, log_agent
from app.graph.nodes.state import AgentState
from app.graph.nodes.models import StrategyAnalysis
from app.tools.nba_client import search_web
from app.prompts.templates import STRATEGY_ANALYST_PROMPT

logger = get_logger("agent.strategy_analyst")


@log_agent("strategy_analyst")
def strategy_analyst_node(state: AgentState) -> dict:
    """
    Agent 5: Tactical scouting report with lineup analysis.

    Pipeline: Web Search (cached) -> LLM Analysis -> Structured Output
    """
    home = state["team_home"]
    away = state["team_away"]

    query = f"{home} vs {away} projected starting lineup key matchups today NBA"
    search_results = search_web(query, max_results=3)

    prompt = STRATEGY_ANALYST_PROMPT.format(
        home_team=home,
        away_team=away,
        search_results=search_results,
    )

    structured_llm = llm.with_structured_output(StrategyAnalysis)

    try:
        result: StrategyAnalysis = structured_llm.invoke([HumanMessage(content=prompt)])
        return {
            "strategy_analysis": result.model_dump_json(),
            "agent_status": {"strategy_analyst": "success"},
        }
    except Exception as e:
        logger.warning(f"Structured output failed, falling back to free text: {e}")
        response = llm.invoke([HumanMessage(content=prompt)])
        return {
            "strategy_analysis": response.content,
            "agent_status": {"strategy_analyst": "fallback"},
        }
