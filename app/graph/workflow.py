"""
LangGraph workflow with graceful degradation.

Features:
- Timeout wrapper: agents that take too long are skipped gracefully
- Fault-tolerant execution: individual agent failures don't crash the pipeline
- Agent health tracking: records which agents succeeded, failed, or timed out
"""
import concurrent.futures
from functools import wraps

from langgraph.graph import StateGraph, START, END

from app.core.config import settings
from app.core.logger import get_logger
from app.graph.nodes.state import AgentState
from app.graph.nodes.recent_analyst import recent_analyst_node
from app.graph.nodes.history_analyst import history_analyst_node
from app.graph.nodes.team_reporter import team_reporter_node
from app.graph.nodes.odds_analyst import odds_analyst_node
from app.graph.nodes.strategy_analyst import strategy_analyst_node
from app.graph.nodes.final_predictor import final_predictor_node

logger = get_logger("workflow")


def with_graceful_degradation(node_func, agent_name: str, output_key: str):
    """
    Wrap an agent node with timeout and error handling.

    If an agent fails or times out:
    - Returns a fallback message instead of crashing
    - Records the failure in agent_status for the final predictor
    - Allows the rest of the pipeline to continue
    """
    @wraps(node_func)
    def wrapper(state: AgentState) -> dict:
        timeout = settings.agent_timeout

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(node_func, state)
                result = future.result(timeout=timeout)
                return result
        except concurrent.futures.TimeoutError:
            logger.error(f"[TIMEOUT] {agent_name} exceeded {timeout}s limit")
            return {
                output_key: f"[{agent_name} timed out after {timeout}s — report unavailable]",
                "agent_status": {agent_name: "timeout"},
            }
        except Exception as e:
            logger.error(f"[FAILED] {agent_name} crashed: {type(e).__name__}: {e}")
            return {
                output_key: f"[{agent_name} failed: {str(e)} — report unavailable]",
                "agent_status": {agent_name: "failed"},
            }

    return wrapper


# Wrap each analyst with graceful degradation
safe_recent_analyst = with_graceful_degradation(
    recent_analyst_node, "recent_analyst", "recent_analysis"
)
safe_history_analyst = with_graceful_degradation(
    history_analyst_node, "history_analyst", "history_analysis"
)
safe_team_reporter = with_graceful_degradation(
    team_reporter_node, "team_reporter", "news_analysis"
)
safe_odds_analyst = with_graceful_degradation(
    odds_analyst_node, "odds_analyst", "odds_analysis"
)
safe_strategy_analyst = with_graceful_degradation(
    strategy_analyst_node, "strategy_analyst", "strategy_analysis"
)

# Build the workflow graph
workflow = StateGraph(AgentState)

# Register nodes (with graceful degradation wrappers)
workflow.add_node("recent_analyst", safe_recent_analyst)
workflow.add_node("history_analyst", safe_history_analyst)
workflow.add_node("team_reporter", safe_team_reporter)
workflow.add_node("odds_analyst", safe_odds_analyst)
workflow.add_node("strategy_analyst", safe_strategy_analyst)
workflow.add_node("final_predictor", final_predictor_node)

# Fan-out: all 5 analysts run in parallel from START
workflow.add_edge(START, "recent_analyst")
workflow.add_edge(START, "history_analyst")
workflow.add_edge(START, "team_reporter")
workflow.add_edge(START, "odds_analyst")
workflow.add_edge(START, "strategy_analyst")

# Fan-in: all analysts feed into the final predictor
workflow.add_edge("recent_analyst", "final_predictor")
workflow.add_edge("history_analyst", "final_predictor")
workflow.add_edge("team_reporter", "final_predictor")
workflow.add_edge("odds_analyst", "final_predictor")
workflow.add_edge("strategy_analyst", "final_predictor")

# Final predictor outputs to END
workflow.add_edge("final_predictor", END)

# Compile the workflow
app_workflow = workflow.compile()

logger.info("Workflow compiled successfully with graceful degradation enabled")
