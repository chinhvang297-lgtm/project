"""
Agent 3: Team Reporter (News & Injuries)

Searches for injury reports and breaking news for both teams
using direct web search for speed and reliability.
"""
from langchain_core.messages import HumanMessage

from app.core.config import llm
from app.core.logger import get_logger, log_agent
from app.graph.nodes.state import AgentState
from app.graph.nodes.models import NewsAnalysis
from app.tools.nba_client import search_web
from app.prompts.templates import TEAM_REPORTER_PROMPT

logger = get_logger("agent.team_reporter")


@log_agent("team_reporter")
def team_reporter_node(state: AgentState) -> dict:
    """
    Agent 3: News and injury investigation.

    Pipeline: 2x Web Search -> LLM Analysis -> Structured Output
    """
    home_team = state["team_home"]
    away_team = state["team_away"]

    # Two focused searches (fast, no ReAct overhead)
    injury_data = search_web(
        f"{home_team} vs {away_team} injury report roster update today NBA", max_results=3
    )
    news_data = search_web(
        f"{home_team} {away_team} latest news trades lineup changes NBA", max_results=2
    )

    combined_intel = f"[Injury Reports]:\n{injury_data}\n\n[Latest News]:\n{news_data}"

    prompt = TEAM_REPORTER_PROMPT.format(
        home_team=home_team,
        away_team=away_team,
    ) + f"\n\n[Search Results]:\n{combined_intel}"

    structured_llm = llm.with_structured_output(NewsAnalysis)
    try:
        result: NewsAnalysis = structured_llm.invoke(
            [HumanMessage(content=prompt)]
        )
        return {
            "news_analysis": result.model_dump_json(),
            "agent_status": {"team_reporter": "success"},
        }
    except Exception as e:
        logger.warning(f"Structured output failed: {e}")
        response = llm.invoke([HumanMessage(content=prompt)])
        return {
            "news_analysis": response.content,
            "agent_status": {"team_reporter": "fallback"},
        }
