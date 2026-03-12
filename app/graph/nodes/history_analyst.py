"""
Agent 2: Historical Matchup Analyst (RAG-enhanced)

Uses the enhanced RAG pipeline (query rewriting + reranking) to
retrieve historical matchup data and produce tactical analysis.
"""
from langchain_core.messages import HumanMessage

from app.core.config import llm
from app.core.logger import get_logger, log_agent
from app.graph.nodes.state import AgentState
from app.graph.nodes.models import HistoryAnalysis
from app.tools.retriever import query_knowledge_base
from app.prompts.templates import HISTORY_ANALYST_PROMPT

logger = get_logger("agent.history_analyst")


@log_agent("history_analyst")
def history_analyst_node(state: AgentState) -> dict:
    """
    Agent 2: RAG-based historical analysis with query rewriting and reranking.

    Pipeline: Query Rewrite -> Multi-query Retrieval -> Rerank -> LLM Analysis -> Structured Output
    """
    home_team = state["team_home"]
    away_team = state["team_away"]

    search_query = f"{home_team} vs {away_team} historical matchup tactics key factors"

    # Enhanced RAG with query rewriting and reranking
    historical_context = query_knowledge_base(search_query, k=3, llm=llm)

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
