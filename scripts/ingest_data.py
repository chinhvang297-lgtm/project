"""
NBA Historical Data Ingestion Script.

Fetches real NBA game data from ESPN's public API and stores it
in a FAISS vector database for RAG retrieval.

Usage: python -m scripts.ingest_data
"""
import sys
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings


PERSIST_DIRECTORY = "./nba_knowledge_db"

TEAMS_CONFIG = [
    {"id": "13", "code": "LAL", "name": "Los Angeles Lakers"},
    {"id": "9",  "code": "GSW", "name": "Golden State Warriors"},
    {"id": "2",  "code": "BOS", "name": "Boston Celtics"},
    {"id": "17", "code": "MIL", "name": "Milwaukee Bucks"},
    {"id": "20", "code": "NYK", "name": "New York Knicks"},
    {"id": "7",  "code": "DEN", "name": "Denver Nuggets"},
    {"id": "21", "code": "PHI", "name": "Philadelphia 76ers"},
    {"id": "16", "code": "MIN", "name": "Minnesota Timberwolves"},
    {"id": "18", "code": "OKC", "name": "Oklahoma City Thunder"},
    {"id": "6",  "code": "DAL", "name": "Dallas Mavericks"},
]

SEASON_YEAR = 2025
SEASON_TYPE = 2


def fetch_team_schedule(team_id: str, team_name: str, team_code: str) -> list[Document]:
    """Fetch a team's completed game results from ESPN API."""
    url = (
        f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/"
        f"teams/{team_id}/schedule?season={SEASON_YEAR}&seasontype={SEASON_TYPE}"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print(f"  Fetching schedule for {team_name}...")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"    ESPN API returned status {response.status_code}")
            return []

        data = response.json()
        events = data.get("events", [])
        docs = []

        for event in events:
            try:
                competition = event["competitions"][0]
                game_date = event.get("date", "Unknown")[:10]
                status = competition.get("status", {}).get("type", {}).get("name", "")

                if status != "STATUS_FINAL":
                    continue

                competitors = competition.get("competitors", [])
                if len(competitors) < 2:
                    continue

                home_team_data = competitors[0]
                away_team_data = competitors[1]
                home_name = home_team_data["team"]["displayName"]
                away_name = away_team_data["team"]["displayName"]

                home_score_str = home_team_data.get("score", "0")
                away_score_str = away_team_data.get("score", "0")
                if isinstance(home_score_str, dict):
                    home_score_str = home_score_str.get("displayValue", "0")
                if isinstance(away_score_str, dict):
                    away_score_str = away_score_str.get("displayValue", "0")

                home_winner = home_team_data.get("winner", False)
                is_home = (home_name == team_name)
                our_score = home_score_str if is_home else away_score_str
                opp_score = away_score_str if is_home else home_score_str
                opponent = away_name if is_home else home_name
                location = "Home" if is_home else "Away"
                team_won = (is_home and home_winner) or (not is_home and not home_winner)

                content = (
                    f"Season: {SEASON_YEAR - 1}-{SEASON_YEAR} NBA Regular Season\n"
                    f"Date: {game_date}\n"
                    f"Team: {team_name} ({team_code})\n"
                    f"Opponent: {opponent}\n"
                    f"Location: {location}\n"
                    f"Result: {'Win' if team_won else 'Loss'} "
                    f"(Score: {our_score}-{opp_score})\n"
                    f"Full Result: {home_name} {home_score_str} - {away_name} {away_score_str}\n"
                    f"Note: Real historical data from ESPN."
                )

                doc = Document(
                    page_content=content,
                    metadata={
                        "source": f"ESPN {team_code} vs {opponent}",
                        "year": str(SEASON_YEAR),
                        "team": team_code,
                        "date": game_date,
                        "opponent": opponent,
                        "result": "W" if team_won else "L",
                    },
                )
                docs.append(doc)
            except (KeyError, IndexError, TypeError):
                continue

        print(f"    Fetched {len(docs)} completed games")
        return docs

    except requests.exceptions.RequestException as e:
        print(f"    Network error: {e}")
        return []


def main():
    print(f"Building NBA knowledge base ({SEASON_YEAR - 1}-{SEASON_YEAR} season)...\n")

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("ERROR: DASHSCOPE_API_KEY not set. Check your .env file.")
        return

    all_docs = []
    for team in TEAMS_CONFIG:
        docs = fetch_team_schedule(team["id"], team["name"], team["code"])
        all_docs.extend(docs)
        time.sleep(0.5)

    if not all_docs:
        print("\nNo data fetched. Check your network connection.")
        return

    print(f"\nEmbedding {len(all_docs)} game records into FAISS vector store...")

    embeddings = DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=api_key,
    )

    # Build FAISS index in batches
    batch_size = 50
    vector_db = None

    for i in range(0, len(all_docs), batch_size):
        batch = all_docs[i: i + batch_size]
        if vector_db is None:
            vector_db = FAISS.from_documents(batch, embeddings)
        else:
            batch_db = FAISS.from_documents(batch, embeddings)
            vector_db.merge_from(batch_db)
        print(f"  Batch {i // batch_size + 1}: embedded {len(batch)} records")
        time.sleep(0.3)

    # Save to disk
    os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
    vector_db.save_local(PERSIST_DIRECTORY)

    print(f"\nKnowledge base built successfully!")
    print(f"  Total records: {len(all_docs)}")
    print(f"  Saved to: {PERSIST_DIRECTORY}/")


if __name__ == "__main__":
    main()
