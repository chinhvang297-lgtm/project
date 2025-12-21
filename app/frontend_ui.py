import streamlit as st
import requests
import json
import time
from datetime import datetime
from streamlit_mermaid import st_mermaid

st.set_page_config(
    page_title="IERG5050 Project: NBA Agent System",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    /* Main Layout */
    .main {
        background-color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Typography */
    h1 { color: #000000; font-weight: 800; padding-bottom: 20px; border-bottom: 1px solid #e5e7eb; }
    h2 { color: #333333; font-weight: 600; margin-top: 50px; margin-bottom: 20px; border-left: 5px solid #333333; padding-left: 15px; }
    h3 { color: #374151; font-weight: 600; margin-top: 30px; }
    p, li { font-size: 1.1rem; line-height: 1.6; color: #374151; }
    
    /* Code block styling fix */
    .stCodeBlock { font-size: 0.95rem; }
    
    /* Divider */
    hr { margin: 40px 0; border-top: 1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/api/v1/predict"



@st.cache_data(ttl=3600)
def fetch_live_nba_schedule():
    """
    Gets today's NBA schedule from ESPN.
    """
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            games = []
            
            for event in data.get('events', []):
                competition = event['competitions'][0]
                date_str = event['date'].split("T")[0]
                
                competitors = competition['competitors']
                home_team = next(t['team']['displayName'] for t in competitors if t['homeAway'] == 'home')
                away_team = next(t['team']['displayName'] for t in competitors if t['homeAway'] == 'away')
                
                games.append({
                    "date": date_str,
                    "home": home_team,
                    "away": away_team
                })
            
            return games
    except Exception as e:
        print(f"Failed to fetch live games: {e}")
        return []
    return []

def render_navbar():
    with st.sidebar:
        st.title("Project Roadmap")
        st.markdown("---")
        st.markdown("""
        **1. Introduction**
        *   [Why & What](#1-motivation-the-complexity-of-sports-prediction)
        *   [The 6-Agent Idea](#2-the-solution-a-6-agent-collaboration-system)
        
        **2. Architecture**
        *   [System Diagram](#3-system-architecture-workflow)
        
        **3. Technical Details**
        *   [Agent 1: Stats & Search](#4-agent-1-recent-performance-analyst)
        *   [Agent 2: RAG (History)](#5-agent-2-the-rag-pipeline-history-analyst)
        *   [Agent 3: News & Tools](#6-agent-3-the-news-reporter-autonomous-tool-calling)
        *   [Agent 4: Betting Odds](#7-agent-4-the-market-analyst-odds)
        *   [Agent 5: Coach & Tactics](#8-agent-5-the-tactical-coach-lineups)
        *   [Agent 6: Final Decision](#9-agent-6-consensus-structured-output)
        
        **4. Live Demo**
        *   [Try the System](#10-live-demonstration)
        
        **5. Infrastructure**
        *   [Backend & Database](#11-backend-infrastructure-database)
        
        **6. Conclusion**
        """)
        st.info("Course: IERG5050\n\nStudent: Shanzi\n\nDate: Dec 21, 2024")


def section_introduction():
    st.title("Full-Stack AI Agent: NBA Prediction System")
    st.markdown("""
    This project is a **Multi-Agent System** that predicts NBA games. It is a full-stack app that uses **Retrieval-Augmented Generation (RAG)**, **LangGraph**, and a **Database**.
    """)

    st.header("1. Motivation: Why is this hard?")
    st.markdown("""
    Predicting sports is difficult for normal AI models. Traditional Machine Learning usually only looks at numbers (Box Scores). They miss the real situation.
    
    **Problems with Old Models:**
    1.  **Context:** They don't know if a player is sick or tired.
    2.  **Style:** They don't understand game tactics (like "Small Ball" vs "Big Lineup").
    3.  **Speed:** They can't see breaking news, like a sudden injury.
    
    **My Goal:** Build a system that thinks like a human expert, not just a calculator.
    """)

def section_concept():
    st.header("2. The Solution: A 6-Agent Collaboration System")
    
    st.info("""
    **The Engine:** I use **Qwen-3-Max** (Alibaba DashScope) as the main LLM. 
    I chose this because it has good logic skills and can read a lot of text (large context window).
    """)

    st.markdown("""
    I use a **Multi-Agent Architecture**. This means I split the job into 6 different roles. It is like having a team of 6 human analysts working together.
    
    **The Team Roles:**
    
    *   **Agent 1 (Stats):** Checks recent data (Win streaks, points).
    *   **Agent 2 (Historian):** Uses **RAG** to find similar past games in the database.
    *   **Agent 3 (Reporter):** Searches the web for breaking news and injuries.
    *   **Agent 4 (Oddsmaker):** Checks betting markets (what people are betting on).
    *   **Agent 5 (Coach):** Looks at starting lineups and game plans.
    *   **Agent 6 (Boss):** The "Brain" that reads all reports and makes the final decision.
    """)

def section_architecture():
    st.header("3. System Architecture & Workflow")
    
    st.markdown("### 3.1 Architecture Diagram")
    st.markdown("This diagram shows how data moves from the User Interface (Frontend) down to the Database.")
    
    code = """
    graph TD
        %% Configuration
        classDef box fill:#f9fafb,stroke:#000,stroke-width:1px,color:#000;
        classDef actor fill:#e5e7eb,stroke:#000,stroke-width:1px,color:#000;
        classDef db fill:#f3f4f6,stroke:#000,stroke-width:1px,color:#000;

        subgraph Frontend ["Frontend Layer (Streamlit)"]
            UI["User Interface"]
        end

        subgraph Backend ["Backend Layer (FastAPI)"]
            API["API Endpoint"]
            DB[("SQLite Database")]
        end

        subgraph Brain ["Control Layer (LangGraph)"]
            Router{"State Router"}
            
            subgraph Agents ["Parallel Agents"]
                direction LR
                A1["Agent 1: Stats"]
                A2["Agent 2: History"]
                A3["Agent 3: News"]
                A4["Agent 4: Odds"]
                A5["Agent 5: Strategy"]
            end

            A6["Agent 6: Decision Maker"]
        end

        subgraph Ext ["External Tools"]
            Web["Tavily Search"]
            Vector["ChromaDB (RAG)"]
        end

        %% Connections
        UI ==>|JSON Request| API
        API ==>|Start Graph| Router

        %% Fan Out
        Router --> A1 & A2 & A3 & A4 & A5

        %% Tool Usage
        A1 & A3 & A4 & A5 -.-o|Search Web| Web
        A2 -.-o|Get Vectors| Vector

        %% Fan In
        A1 & A2 & A3 & A4 & A5 -->|Report| A6

        %% Output
        A6 ==>|Structured JSON| API
        A6 -.->|Save Record| DB

        %% Styling
        class UI,API,Router box
        class A1,A2,A3,A4,A5,A6 actor
        class DB,Web,Vector db
    """
    st_mermaid(code, height="550px")

    st.markdown("### 3.2 How it works (Step-by-Step)")
    st.markdown("""
    The system has **three main layers**. 
    Here is what happens when you click "Predict":
    """)

    st.info("**Layer 1: Input (Frontend/Backend)**")
    st.markdown("""
    **The Process:**
    1.  You pick a game in the Streamlit UI.
    2.  The Frontend sends the team names (JSON) to the Backend.
    3.  It uses an asynchronous `POST` request (it doesn't block the screen).
    
    **Why?**
    Separating Frontend and Backend is good design (**Microservices**). 
    I can update the AI without breaking the website.
    """)

    st.info("**Layer 2: Managing the Agents**")
    st.markdown("""
    **The Router:**
    The request goes to the **LangGraph State Router**. This is like a traffic controller.
    It creates a shared memory (`AgentState`).
    
    **Running in Parallel (Fast):**
    Instead of running agents one by one, the system runs 5 agents **at the same time**.
    *   **Agents 1, 3, 4, 5:** Go to the Internet (using **Tavily Search API**) to get live data.
    *   **Agent 2:** Goes to the local database (**ChromaDB**) to look up history (RAG).
    
    **Benefit:** Because they run together, it takes ~15 seconds instead of 60 seconds.
    """)

    st.info("**Layer 3: Combining Results & Saving**")
    st.markdown("""
    **Combining (Aggregation):**
    When all 5 agents finish, they save their reports to the shared memory.
    
    **The Decision:**
    **Agent 6 (The Boss)** reads all 5 reports. It checks for conflicts. 
    *   *Example:* If "Stats" say Team A wins, but "News" says Team A is injured, Agent 6 will listen to the News.
    
    **Saving Data:**
    Finally, the system does two things:
    1.  Sends the answer back to the Frontend.
    2.  Saves the full report to the **SQLite Database**. This is important to check accuracy later.
    """)

    st.markdown("### 3.3 Why did I build it this way?")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("**1. Modular Agents**")
        st.markdown("Each agent has one job. It is easy to fix. If stats are wrong, I only fix Agent 1.")
    
    with c2:
        st.markdown("**2. Asynchronous API**")
        st.markdown("Using `async` lets the server handle many users at once. It is efficient.")
        
    with c3:
        st.markdown("**3. Vector Database**")
        st.markdown("Normal databases can't search by 'meaning'. Vector DB lets me find games with similar styles.")

def section_deep_dive_1():
    st.header("4. Agent 1: Stats & Recent Form")
    
    st.markdown("### 4.1 Getting the Data")
    st.markdown("""
    **Problem:** Official NBA APIs are often expensive or hard to get.
    **Solution:** Agent 1 uses **Tavily Search Tool**. It searches the web like a human to find scores on sites like ESPN or CBS.
    """)
    
    st.code("""
# app/tools/nba_client.py

def get_recent_games_stats(team_name: str, last_n: int = 5):
    # Search the web for recent scores
    search = TavilySearchResults(max_results=5)
    query = f"{team_name} last {last_n} games results scores and stats"
    
    # Returns text from the web
    return search.invoke(query)
    """, language="python")

    st.markdown("### 4.2 Designing the Prompt")
    st.markdown("""
    The search result is just text. The **Qwen LLM** reads this text.
    I wrote a prompt to make the AI look for specific things: **Win/Loss Record** and **Points Scored**.
    It must also tell me the team's "Momentum" (are they getting better or worse?).
    """)

    st.code("""
# app/graph/nodes/recent_analyst.py

def recent_analyst_node(state: AgentState):
    # ... (Fetching data) ...

    prompt = f\"\"\"
    You are a senior NBA performance analyst. 
    
    [Data]: {raw_web_data}

    Requirements:
    1. Look at wins/losses and scoring.
    2. Check the Point Differential (PLUS_MINUS).
    3. CRITICAL: Don't just list numbers; tell me who has better momentum.
    \"\"\"

    return llm.invoke([HumanMessage(content=prompt)])
    """, language="python")

def section_deep_dive_2():
    st.header("5. Agent 2: The RAG Pipeline (History)")
    
    st.markdown("""
    **Problem:** AI models sometimes "hallucinate" (make up fake scores).
    **Solution:** I used **RAG (Retrieval-Augmented Generation)**. The AI must read from a trusted database, not just guess.
    """)

    st.markdown("### 5.1 Step 1: Loading Data (Ingestion)")
    st.markdown("""
    I wrote a script `scripts/ingest_data.py`. 
    1.  It gets real data from Basketball-Reference.
    2.  It turns game records into **Vectors** (numbers that represent meaning).
    3.  It saves them into **ChromaDB** (Local Database).
    """)
    
    st.code("""
# scripts/ingest_data.py

# Create a text summary for each game
content = (
    f"Date: {date}\\n"
    f"Matchup: {team} vs {opponent}\\n"
    f"Result: {result} (Score: {team_pts}-{opp_pts})\\n"
    f"Note: Real historical record."
)

# Convert to Vector and save to ChromaDB
doc = Document(page_content=content, metadata={"source": "B-Ref"})
vector_db.add_documents([doc])
    """, language="python")
    

    st.markdown("### 5.2 Step 2: Searching while Running")
    st.markdown("""
    When predicting a game, Agent 2 asks ChromaDB. It finds the **Top 3 most similar past games**.
    I put these real facts into the prompt.
    """)

    st.code("""
# app/graph/nodes/history_analyst.py

def history_analyst_node(state: AgentState):
    # 1. Search Vector DB for similar games
    query = f"{state['team_home']} vs {state['team_away']} historical matchup"
    results = query_knowledge_base(query, k=3)

    # 2. Put facts into the Prompt
    prompt = f\"\"\"
    You are an NBA Historian.
    
    [Real Historical Data]:
    {results}
    
    Based ONLY on the data above, analyze the trends.
    \"\"\"

    return llm.invoke(prompt)
    """, language="python")

    st.success("Result: The analysis is based on real facts. No fake info.")

def section_deep_dive_3():
    st.header("6. Agent 3: News Reporter (Thinking & Acting)")
    
    st.markdown("### 6.1 The \"ReAct\" Pattern")
    st.markdown("""
    Agent 3 is smart. It is **autonomous** (works by itself).
    It follows the **ReAct (Reason + Act)** loop:
    1.  **Reason:** "Do I need to check for injuries?"
    2.  **Act:** If yes, use the Search Tool.
    3.  **Observe:** Read the results.
    """)

    st.markdown("### 6.2 The Code")
    st.markdown("""
    I used **Tool Binding**. The LLM decides *if* it needs to call the tool.
    This saves money because it only searches when it needs to.
    """)

    st.code("""
# app/graph/nodes/team_reporter.py

# Give the agent a tool
llm_with_tools = llm.bind_tools([search_tool])

def team_reporter_node(state: AgentState):
    prompt = f"Check injury reports for {state['team_home']}."
    
    # AI thinks...
    response = llm_with_tools.invoke([HumanMessage(content=prompt)])

    # Check if AI wants to use the tool
    if response.tool_calls:
        print("Agent decided to search web...")
        # Run the tool and give results back to AI
        ...
    else:
        # AI returns answer directly
        return response
    """, language="python")

def section_deep_dive_4():
    st.header("7. Agent 4: Market Analyst (Odds)")
    
    st.markdown("""
    **Concept:** Betting odds show what the public thinks.
    **Agent 4** looks at the market. It translates math (odds) into simple words.
    """)
    
    st.markdown("### 7.1 How it thinks")
    st.markdown("""
    The agent explains:
    *   **The Spread:** The expected point gap (e.g., -7.5 means the team is a strong favorite).
    *   **The Total:** How many total points will be scored.
    """)

    st.code("""
# app/graph/nodes/odds_analyst.py

def odds_analyst_node(state):
    # Search for betting lines
    market_data = search_tool.invoke("betting odds spread moneyline")
    
    prompt = f\"\"\"
    You are a professional sports bettor.
    [Market Data]: {market_data}
    
    Tasks:
    1. Who is the 'Favorite' and who is the 'Underdog'?
    2. Explain what the 'Spread' means for this game.
    \"\"\"
    
    return llm.invoke(prompt)
    """, language="python")

def section_deep_dive_5():
    st.header("8. Agent 5: Tactical Coach (Lineups)")
    
    st.markdown("""
    **Concept:** Agent 5 looks for **Matchup Problems**.
    Stats are about the past, but Lineups are about tonight.
    """)
    
    st.markdown("### 8.1 Finding Mismatches")
    st.markdown("""
    The agent searches for starting lineups. It checks:
    *   **Size:** Is one team much taller?
    *   **Defense:** Who is guarding the star player?
    """)

    st.code("""
# app/graph/nodes/strategy_analyst.py

def strategy_analyst_node(state):
    # Get lineups
    lineups = search_tool.invoke("projected starting lineup")
    
    prompt = f\"\"\"
    You are an NBA Head Coach.
    [Lineups]: {lineups}
    
    Analyze:
    1. Who guards the opposing star player?
    2. Which team has a better bench unit?
    \"\"\"
    
    return llm.invoke(prompt)
    """, language="python")

def section_deep_dive_6():
    st.header("9. Agent 6: Consensus & Structured Output")
    st.markdown("""
    **Agent 6** makes the final choice. It reads reports from the other 5 agents.
    It decides what is most important (e.g., Injury News is more important than History).
    
    **Structured Output:**
    I used **Pydantic**. This forces the AI to reply in a strict JSON format. 
    This ensures the website can display the data correctly every time.
    """)
    
    st.code("""
# app/graph/nodes/final_predictor.py

class GamePrediction(BaseModel):
    winner: str = Field(description="Winning team name")
    win_probability: float = Field(description="0-100 float")
    key_factors: list[str]
    summary: str

# Force Structured Output (JSON)
structured_llm = llm.with_structured_output(GamePrediction)
    """, language="python")

def section_demo():
    st.header("10. Live Demonstration")
    st.markdown("""
    Let's see the system in action.
    Select a game below and click **"Run Prediction"**. 
    You will see the system running the agents step-by-step.
    """)
    
    st.markdown("### Control Panel")
    
    with st.spinner("Getting today's NBA schedule from ESPN..."):
        live_schedule = fetch_live_nba_schedule()
        
    if live_schedule:
        st.success(f"Loaded {len(live_schedule)} live games for today!")
        schedule_source = live_schedule
    else:
        st.warning("Could not find live games (or no games today). Using backup schedule for demo.")
        schedule_source = [
            {"date": "2024-12-25", "home": "Golden State Warriors", "away": "Denver Nuggets"},
            {"date": "2024-12-25", "home": "Boston Celtics", "away": "Philadelphia 76ers"},
            {"date": "2024-12-25", "home": "Los Angeles Lakers", "away": "Boston Celtics"},
            {"date": "2024-12-25", "home": "New York Knicks", "away": "Milwaukee Bucks"},
        ]
    
    col_sel, col_btn = st.columns([3, 1])
    
    with col_sel:
        options = [f"{g['date']} | {g['away']} @ {g['home']}" for g in schedule_source]
        selected_option = st.selectbox("Select a Matchup:", options, label_visibility="collapsed")
        index = options.index(selected_option)
        selected_game = schedule_source[index]
        
    with col_btn:
        start_prediction = st.button("Run Prediction", type="primary", use_container_width=True)
    if start_prediction:
        status_box = st.status("**System Status: Starting Agents...**", expanded=True)
        
        try:
            status_box.write("Router: Connecting to Backend Server...")
            time.sleep(0.5)
            
            payload = {"team_home": selected_game["home"], "team_away": selected_game["away"]}
            start_ts = time.time()
            response = requests.post(API_URL, json=payload, timeout=120)
            end_ts = time.time()
            
            if response.status_code == 200:
                data = response.json()
                details = data.get("prediction_details", {})
                status_box.write("LangGraph: Running 5 Agents together...")
                time.sleep(0.3)
                status_box.write(f"Agent 1 (Stats): Checked {selected_game['home']} momentum.")
                status_box.write(f"Agent 2 (History): Found past games via RAG.")
                status_box.write("Agent 3 (News): Checked injury reports.")
                status_box.write("Agent 4 (Odds): Checked betting lines.")
                status_box.write(f"Agent 6: Final decision made in {end_ts - start_ts:.2f}s.")
                
                status_box.update(label="Analysis Complete!", state="complete", expanded=False)
                
                st.markdown("### Final Prediction Report")
                c1, c2 = st.columns(2)
                c1.metric("Predicted Winner", details.get("winner", "Unknown"))
                c2.metric("Win Probability", f"{details.get('win_probability', 0)}%")
                
                st.subheader("Predicted Score")
                st.write(details.get("score_prediction", "N/A"))
                
                st.info(f"**Chief Analyst Summary:**\n\n{details.get('summary', 'No summary provided.')}")
                
                if details.get("key_factors"):
                    st.markdown("**Key Reasons:**")
                    for factor in details["key_factors"]:
                        st.markdown(f"- {factor}")
                        
                st.success("Persistence: Result saved to Database for tracking.")
                
            else:
                status_box.update(label="Error", state="error")
                st.error(f"Backend API Error: {response.text}")
                
        except Exception as e:
            status_box.update(label="Connection Failed", state="error")
            st.error(f"Could not connect to backend. Is the FastAPI server running? \n\nError: {e}")

def section_infrastructure():
    st.header("11. Backend Infrastructure & Database")
    st.markdown("""
    This system is built for real use, not just as a toy.
    
    1.  **FastAPI Server:** It wraps the AI logic in an API. This keeps the website fast and separate from the heavy AI work.
    2.  **SQLite Database:** I use SQLAlchemy to store every prediction.
    
    **Why use a Database?**
    It creates a **Feedback Loop**. We can compare our predictions with real results later. This helps us see how accurate the AI is.
    """)
    
    st.code("""
# app/db/models.py
class PredictionRecord(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    team_home = Column(String)
    team_away = Column(String)
    final_result = Column(Text) # Stores the full JSON analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    """, language="python")

def section_conclusion():
    st.markdown("---")
    st.header("12. Conclusion")
    st.markdown("""
    This project successfully builds an **Agentic AI Workflow**.
    
    **Key Achievements:**
    *   **Groundedness:** Uses RAG and Database to stop "hallucinations".
    *   **Speed:** Uses Parallel Agents to be fast.
    *   **Reliability:** Uses Structured Output for clean data.
    
    This design can be used for other things too, like Finance or Healthcare.
    Thank you.
    """)
    
def main():
    render_navbar()
    
    section_introduction()
    section_concept()
    section_architecture()
    
    st.markdown("---")
    section_deep_dive_1()
    section_deep_dive_2()
    section_deep_dive_3()
    section_deep_dive_4()
    section_deep_dive_5()
    section_deep_dive_6()
    
    st.markdown("---")
    section_demo()
    
    st.markdown("---")
    section_infrastructure()
    section_conclusion()

if __name__ == "__main__":
    main()