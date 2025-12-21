# /Users/shanzi/iemsProject/app/graph/workflow.py
from langgraph.graph import StateGraph, START, END

from app.graph.nodes.state import AgentState
from app.graph.nodes.recent_analyst import recent_analyst_node
from app.graph.nodes.history_analyst import history_analyst_node
from app.graph.nodes.team_reporter import team_reporter_node
from app.graph.nodes.odds_analyst import odds_analyst_node
from app.graph.nodes.strategy_analyst import strategy_analyst_node
from app.graph.nodes.final_predictor import final_predictor_node

workflow = StateGraph(AgentState)

workflow.add_node("recent_analyst", recent_analyst_node)
workflow.add_node("history_analyst", history_analyst_node)
workflow.add_node("team_reporter", team_reporter_node)
workflow.add_node("odds_analyst", odds_analyst_node)
workflow.add_node("strategy_analyst", strategy_analyst_node)
workflow.add_node("final_predictor", final_predictor_node)

workflow.add_edge(START, "recent_analyst")
workflow.add_edge(START, "history_analyst")
workflow.add_edge(START, "team_reporter")
workflow.add_edge(START, "odds_analyst")
workflow.add_edge(START, "strategy_analyst")

workflow.add_edge("recent_analyst", "final_predictor")
workflow.add_edge("history_analyst", "final_predictor")
workflow.add_edge("team_reporter", "final_predictor")
workflow.add_edge("odds_analyst", "final_predictor")
workflow.add_edge("strategy_analyst", "final_predictor")

workflow.add_edge("final_predictor", END)

app_headless = workflow.compile()