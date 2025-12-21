# /Users/shanzi/iemsProject/app/graph/nodes/history_analyst.py
from langchain_core.messages import HumanMessage
from app.core.config import llm
from app.graph.nodes.state import AgentState
from app.tools.retriever import query_knowledge_base

def history_analyst_node(state: AgentState):
    """
    Agent 2: Historical Matchup Analyst (RAG)
    """
    print("--- [Agent 2] Starting Historical Analysis (RAG) ---")

    home_team = state["team_home"]
    away_team = state["team_away"]

    search_query = f"{home_team} vs {away_team} historical matchup tactics key factors"

    historical_context = query_knowledge_base(search_query, k=3)

    prompt = f"""
    You are an NBA Historical Tactical Analyst.
    You possess internal tactical databases regarding {home_team} and {away_team}.

    Here are the [Historical References] retrieved from the database:
    =========================================
    {historical_context}
    =========================================

    Based on the above data, please analyze:
    1. What were the key factors determining victory in historical matchups? (e.g., who defended whom effectively?)
    2. Are there any stylistic suppression relationships between the teams?
    3. Based on historical experience, predict the tactical trend of this game.

    Please output a professional tactical analysis report (within 200 words).
    """

    print("AI is analyzing history context...")
    response = llm.invoke([HumanMessage(content=prompt)])

    return {"history_analysis": response.content}