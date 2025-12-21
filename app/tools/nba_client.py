# /Users/shanzi/iemsProject/app/tools/nba_client.py
from langchain_community.tools.tavily_search import TavilySearchResults

def get_recent_games_stats(team_name: str, last_n: int = 5):
    search = TavilySearchResults(max_results=5)
    
    query = f"{team_name} last {last_n} games results scores and stats"
    
    try:
        print(f"   🔍 [Agent 1 Tool] Searching web for recent stats of {team_name} (Bypassing NBA API)...")
        results = search.invoke(query)
        
        return str(results)
        
    except Exception as e:
        print(f"❌ Failed to fetch recent stats: {e}")
        return f"Error fetching recent stats: {e}"