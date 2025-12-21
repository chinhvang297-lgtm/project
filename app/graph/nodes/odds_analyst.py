# /Users/shanzi/iemsProject/app/graph/nodes/odds_analyst.py
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from app.core.config import llm
from app.graph.nodes.state import AgentState

search_tool = TavilySearchResults(max_results=3)

def odds_analyst_node(state: AgentState):
    """
    Agent 4: Odds and Market Analyst
    """
    print("--- [Agent 4] Checking Betting Odds & Market Sentiment ---")

    home = state["team_home"]
    away = state["team_away"]

    query = f"{home} vs {away} odds prediction betting spread moneyline today"
    try:
        search_results = search_tool.invoke(query)
    except Exception as e:
        search_results = f"Search failed: {e}"

    prompt = f"""
    You are a professional sports betting analyst.

    [Match]: {home} (Home) vs {away} (Away)
    [Market Data Found]:
    {search_results}

    Please analyze market sentiment:
    1. Which team is the Underdog and which is the Favorite?
    2. What is the Spread? What does this imply about the gap perceived by the bookmakers?
    3. Are there significant public betting trends (money flow)?

    Output a brief market analysis report (within 150 words).
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"odds_analysis": response.content}