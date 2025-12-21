# /Users/shanzi/iemsProject/app/graph/nodes/team_reporter.py
import json
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from app.core.config import llm
from app.graph.nodes.state import AgentState

search_tool = TavilySearchResults(max_results=3)

llm_with_tools = llm.bind_tools([search_tool])

def team_reporter_node(state: AgentState):
    """
    Agent 3: Team Reporter (News & Injuries)
    """
    print("--- [Agent 3] Starting News Investigation ---")

    home_team = state["team_home"]
    away_team = state["team_away"]

    prompt = f"""
    You are an NBA team reporter.
    You need to investigate the latest injury reports and important trade rumors for {home_team} and {away_team}.

    If you do not have exact information, you [MUST] use the search tool to query.
    Search keywords should be specific, e.g., "{home_team} injury report today".

    [Final Output Requirements]:
    1. Report the injury status of core players for both teams.
    2. Based on the injury situation and news intelligence, provide a [preliminary prediction] of the game outcome.
       (e.g., "Due to key player absence, I am bearish on...")
    """

    print("AI is thinking...")
    response = llm_with_tools.invoke([HumanMessage(content=prompt)])

    if response.tool_calls:
        print(f"Agent decided to search. Tool Call Count: {len(response.tool_calls)}")

        messages = [HumanMessage(content=prompt), response]

        for tool_call in response.tool_calls:
            search_query = tool_call['args']
            call_id = tool_call['id']
            print(f"    - Processing Call {call_id}: {search_query}")

            try:
                search_result = search_tool.invoke(search_query)
            except Exception as e:
                search_result = f"Search failed: {e}"

            messages.append(
                ToolMessage(
                    tool_call_id=call_id,
                    content=str(search_result)
                )
            )

        print("All searches done. Summarizing news and predicting...")
        final_response = llm_with_tools.invoke(messages)
        content = final_response.content

    else:
        print("Agent decided NOT to search.")
        content = response.content

    return {"news_analysis": content}