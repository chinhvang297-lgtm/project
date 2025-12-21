# /Users/shanzi/iemsProject/app/graph/nodes/recent_analyst.py
from langchain_core.messages import HumanMessage
from app.core.config import llm
from app.graph.nodes.state import AgentState
from app.tools.nba_client import get_recent_games_stats

def recent_analyst_node(state: AgentState):
    """
    Agent 1: Recent Performance Analysis Node
    """
    print("--- [Agent 1] Starting Recent Analysis ---")

    home_team = state["team_home"]
    away_team = state["team_away"]

    print(f"Fetching stats for {home_team} & {away_team}...")
    home_stats = get_recent_games_stats(home_team, last_n=5)
    away_stats = get_recent_games_stats(away_team, last_n=5)

    prompt = f"""
    You are a senior NBA performance analyst. Please analyze the recent status of the following two teams.

    [Home Team: {home_team}]
    {home_stats}

    [Away Team: {away_team}]
    {away_stats}

    Please analyze based on win/loss records, scoring ability (PTS), and point differential (PLUS_MINUS).
    Do not just list data; tell me which team has the stronger momentum currently.
    Please provide a brief, sharp analysis report (within 200 words).
    """

    print("Asking Qwen for analysis...")
    response = llm.invoke([HumanMessage(content=prompt)])

    return {"recent_analysis": response.content}