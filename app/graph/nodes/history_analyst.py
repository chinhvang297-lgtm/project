"""
Agent 2: Historical Matchup Analyst (RAG-enhanced)

Uses FAISS vector store to retrieve historical matchup data,
supplemented by web search for additional context.
"""
from langchain_core.messages import HumanMessage

from app.core.config import llm
from app.core.logger import get_logger, log_agent
from app.graph.nodes.state import AgentState
from app.graph.nodes.models import HistoryAnalysis
from app.tools.retriever import query_knowledge_base
from app.tools.nba_client import search_web
from app.prompts.templates import HISTORY_ANALYST_PROMPT

logger = get_logger("agent.history_analyst")


@log_agent("history_analyst")
def history_analyst_node(state: AgentState) -> dict:
    """
    Agent 2: RAG + web search historical analysis.

    Pipeline: RAG Retrieval -> Web Search Supplement -> LLM Analysis -> Structured Output
    """
    home_team = state["team_home"]
    away_team = state["team_away"]

    # Stage 1: RAG retrieval from FAISS knowledge base
    rag_query = f"{home_team} vs {away_team} historical matchup tactics key factors"
    rag_context = query_knowledge_base(rag_query, k=3)

    # Stage 2: Supplement with web search for recent head-to-head
    web_query = f"{home_team} vs {away_team} head to head history record"
    web_context = search_web(web_query, max_results=2)

    # Combine both sources
    historical_context = f"[RAG Database Results]:\n{rag_context}\n\n[Web Search Results]:\n{web_context}"

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
