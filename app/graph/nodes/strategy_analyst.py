# /Users/shanzi/iemsProject/app/graph/nodes/strategy_analyst.py
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from app.core.config import llm
from app.graph.nodes.state import AgentState

search_tool = TavilySearchResults(max_results=3)

def strategy_analyst_node(state: AgentState):
    """
    Agent 5: Strategy and Matchup Coach
    """
    print("--- [Agent 5] Analyzing Matchups & Lineups ---")

    home = state["team_home"]
    away = state["team_away"]

    query = f"{home} vs {away} projected starting lineup key matchups today"
    try:
        search_results = search_tool.invoke(query)
    except Exception as e:
        search_results = f"Search failed: {e}"

    prompt = f"""
    You are an NBA Tactical Coach.

    [Match]: {home} vs {away}
    [Intel]: {search_results}

    Please analyze key matchups:
    1. Are there any obvious weaknesses in the projected starting lineups? (e.g., opposing guard is too fast, our center is too slow)
    2. Who will defend the opposing team's star player?
    3. Which team has better bench depth?

    Output a tactical matchup analysis report (within 150 words).
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"strategy_analysis": response.content}