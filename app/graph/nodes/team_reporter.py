"""
Agent 3: Team Reporter (News & Injuries)

Autonomous agent that uses ReAct pattern (Reason + Act) to decide
whether to search for information, with tool calling support.
"""
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from app.core.config import llm
from app.core.logger import get_logger, log_agent
from app.graph.nodes.state import AgentState
from app.graph.nodes.models import NewsAnalysis
from app.prompts.templates import TEAM_REPORTER_PROMPT

logger = get_logger("agent.team_reporter")

search_tool = TavilySearchResults(max_results=3)
llm_with_tools = llm.bind_tools([search_tool])


@log_agent("team_reporter")
def team_reporter_node(state: AgentState) -> dict:
    """
    Agent 3: Autonomous news investigation using ReAct pattern.

    Pipeline: Prompt -> LLM decides to search (or not) -> Execute tools -> Summarize -> Structured Output
    """
    home_team = state["team_home"]
    away_team = state["team_away"]

    prompt = TEAM_REPORTER_PROMPT.format(
        home_team=home_team,
        away_team=away_team,
    )

    # Phase 1: LLM reasons about what to do (ReAct: Reason)
    response = llm_with_tools.invoke([HumanMessage(content=prompt)])

    # Phase 2: Execute tool calls if the LLM decided to search (ReAct: Act)
    if response.tool_calls:
        logger.info(f"Agent decided to search. Tool calls: {len(response.tool_calls)}")
        messages = [HumanMessage(content=prompt), response]

        for tool_call in response.tool_calls:
            search_query = tool_call["args"]
            call_id = tool_call["id"]
            logger.info(f"Executing tool call {call_id}: {search_query}")

            try:
                search_result = search_tool.invoke(search_query)
            except Exception as e:
                logger.warning(f"Tool call failed: {e}")
                search_result = f"Search failed: {e}"

            messages.append(
                ToolMessage(tool_call_id=call_id, content=str(search_result))
            )

        # Phase 3: LLM synthesizes results (ReAct: Observe + Conclude)
        final_response = llm_with_tools.invoke(messages)
        content = final_response.content
    else:
        logger.info("Agent decided NOT to search (has sufficient knowledge)")
        content = response.content

    # Phase 4: Structure the output
    structured_llm = llm.with_structured_output(NewsAnalysis)
    try:
        structuring_prompt = f"""
        Based on the following news analysis, produce a structured report:

        {content}

        Match: {home_team} vs {away_team}
        """
        result: NewsAnalysis = structured_llm.invoke(
            [HumanMessage(content=structuring_prompt)]
        )
        return {
            "news_analysis": result.model_dump_json(),
            "agent_status": {"team_reporter": "success"},
        }
    except Exception as e:
        logger.warning(f"Structured output failed: {e}")
        return {
            "news_analysis": content,
            "agent_status": {"team_reporter": "fallback"},
        }
