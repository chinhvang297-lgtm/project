"""
NBA data client with retry mechanism and caching.

Uses Tavily Search to fetch real-time NBA stats from the web,
with tenacity retry for resilience against transient failures.
"""
from langchain_community.tools.tavily_search import TavilySearchResults
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.logger import get_logger
from app.core.cache import search_cache, TTLCache
from app.core.config import settings

logger = get_logger("tools.nba_client")


@retry(
    stop=stop_after_attempt(settings.agent_max_retries + 1),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.warning(
        f"Search retry #{retry_state.attempt_number} after error"
    ),
)
def _search_with_retry(search_tool, query: str) -> str:
    """Execute a Tavily search with automatic retry on failure."""
    return str(search_tool.invoke(query))


def get_recent_games_stats(team_name: str, last_n: int = 5) -> str:
    """
    Fetch recent game stats for an NBA team via web search.

    Features:
    - Result caching to avoid redundant searches
    - Automatic retry with exponential backoff
    """
    cache_key = TTLCache._make_key("recent_stats", team_name, last_n)
    cached = search_cache.get(cache_key)
    if cached:
        logger.info(f"Cache hit for recent stats: {team_name}")
        return cached

    search = TavilySearchResults(max_results=settings.tavily_max_results)
    query = f"{team_name} last {last_n} games results scores and stats NBA"

    try:
        logger.info(f"Searching web for recent stats: {team_name}")
        result = _search_with_retry(search, query)
        search_cache.set(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Failed to fetch recent stats for {team_name}: {e}")
        return f"Error fetching recent stats: {e}"


def search_web(query: str, max_results: int = 3) -> str:
    """
    General-purpose web search with caching and retry.

    Used by multiple agents for odds, lineups, and news searches.
    """
    cache_key = TTLCache._make_key("web_search", query, max_results)
    cached = search_cache.get(cache_key)
    if cached:
        logger.info(f"Cache hit for web search: {query[:50]}...")
        return cached

    search = TavilySearchResults(max_results=max_results)

    try:
        logger.info(f"Web search: {query[:50]}...")
        result = _search_with_retry(search, query)
        search_cache.set(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Search failed: {e}"
