# /Users/shanzi/iemsProject/scripts/ingest_data.py
import sys
import os
import time
import requests
import pandas as pd
from io import StringIO
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.documents import Document
from app.tools.retriever import get_vector_store

def fetch_real_data_from_bref():
    print("🚀 Starting to build NBA tactical database (Source: Basketball-Reference Real Data)...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    teams_config = [
        {"code": "LAL", "name": "Los Angeles Lakers"},
        {"code": "GSW", "name": "Golden State Warriors"}
    ]
    season = 2024
    
    docs = []
    
    for team in teams_config:
        url = f"https://www.basketball-reference.com/teams/{team['code']}/{season}_games.html"
        print(f"📡 [Spoofing Browser] Fetching real schedule for {team['name']}...")
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Request refused, status code: {response.status_code}")
                continue
                
            html_data = StringIO(response.text)
            dfs = pd.read_html(html_data, match="Date")
            games_df = dfs[0]
            
            games_df = games_df[games_df['Date'] != 'Date']
            games_df = games_df.dropna(subset=['Tm', 'Opp'])
            
            count = 0
            for _, row in games_df.iterrows():
                date = row.get('Date', 'Unknown')
                opponent = row.get('Opponent', 'Unknown')
                result = row.get('Unnamed: 7', '') 
                if pd.isna(result): result = "Unknown"
                
                team_pts = row.get('Tm', '0')
                opp_pts = row.get('Opp', '0')
                
                content = (
                    f"Season: {season-1}-{season}\n"
                    f"Date: {date}\n"
                    f"Team: {team['name']} ({team['code']})\n"
                    f"Opponent: {opponent}\n"
                    f"Result: {result} (Team Points: {team_pts}, Opponent Points: {opp_pts})\n"
                    f"Note: Real historical data record."
                )
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": f"B-Ref {team['code']} vs {opponent}",
                        "year": str(season),
                        "team": team['code']
                    }
                )
                docs.append(doc)
                count += 1
            
            print(f"   ✅ Successfully fetched {count} games.")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error processing {team['name']}: {e}")

    if docs:
        print(f"\n💾 Writing {len(docs)} real data records to vector database...")
        try:
            vector_db = get_vector_store()
            batch_size = 50
            for i in range(0, len(docs), batch_size):
                batch = docs[i:i+batch_size]
                vector_db.add_documents(batch)
            print("✅ Real data build complete! Persisted to ./nba_knowledge_db")
        except Exception as e:
            print(f"❌ Database write error: {e}")
    else:
        print("⚠️ No data fetched. IP might be blocked by the site. Try connecting via mobile hotspot.")

if __name__ == "__main__":
    fetch_real_data_from_bref()