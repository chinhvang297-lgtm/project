"""
NBA Game Predictor - Streamlit Frontend

Features:
- Date picker with ESPN game schedule
- Live agent status tracking via SSE streaming (using Streamlit native components)
- Styled result display
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta

st.set_page_config(
    page_title="NBA Game Predictor",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS (only for result cards, not for agent tracker) ───
st.markdown("""
<style>
    .block-container { max-width: 960px; padding-top: 2rem; }
    .hero-title {
        text-align: center; font-size: 2.8rem; font-weight: 800;
        background: linear-gradient(135deg, #f97316, #ef4444);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        text-align: center; color: #9ca3af; font-size: 1.05rem; margin-bottom: 2.5rem;
    }
    .game-card {
        background: linear-gradient(145deg, #1e293b, #1a1f2e);
        border: 1px solid #334155; border-radius: 16px;
        padding: 28px 32px; margin-bottom: 20px;
    }
    .game-card:hover { border-color: #f97316; }
    .vs-text { text-align: center; font-size: 1.1rem; color: #64748b; font-weight: 700; letter-spacing: 3px; }
    .team-name { font-size: 1.5rem; font-weight: 700; color: #f1f5f9; text-align: center; padding: 6px 0; }
    .team-label { text-align: center; font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 2px; }
    .result-card {
        background: linear-gradient(145deg, #1e293b, #1a1f2e);
        border: 1px solid #334155; border-radius: 16px; padding: 24px; text-align: center;
    }
    .result-card-winner {
        background: linear-gradient(145deg, #1a2e1a, #1e293b);
        border: 1px solid #22c55e; border-radius: 16px; padding: 24px; text-align: center;
    }
    .result-label { font-size: 0.8rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 4px; }
    .result-value { font-size: 2rem; font-weight: 800; color: #f1f5f9; }
    .result-value-green { font-size: 2rem; font-weight: 800; color: #22c55e; }
    .result-value-orange { font-size: 2rem; font-weight: 800; color: #f97316; }
    .summary-box {
        background: linear-gradient(145deg, #1e293b, #1a1f2e);
        border-left: 4px solid #f97316; border-radius: 0 12px 12px 0;
        padding: 20px 24px; margin: 16px 0; color: #e2e8f0; font-size: 1.05rem; line-height: 1.7;
    }
    .factor-chip {
        display: inline-block; background: #1e293b; border: 1px solid #334155;
        border-radius: 8px; padding: 8px 14px; margin: 4px; color: #e2e8f0; font-size: 0.9rem;
    }
    .footer {
        text-align: center; color: #4b5563; font-size: 0.8rem;
        margin-top: 60px; padding: 20px 0; border-top: 1px solid #1f2937;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/api/v1/predict"
STREAM_URL = "http://127.0.0.1:8000/api/v1/predict/stream"

AGENT_META = {
    "recent_analyst": {"icon": "1", "name": "Recent Stats Analyst", "desc": "Analyzing recent game performance"},
    "history_analyst": {"icon": "2", "name": "Historical Matchup (RAG)", "desc": "Searching vector database + web"},
    "team_reporter": {"icon": "3", "name": "News & Injury Reporter", "desc": "Scanning injury reports & news"},
    "odds_analyst": {"icon": "4", "name": "Betting Odds Analyst", "desc": "Evaluating market odds & spreads"},
    "strategy_analyst": {"icon": "5", "name": "Tactical Strategy Analyst", "desc": "Analyzing tactical matchups"},
    "final_predictor": {"icon": "6", "name": "Final Predictor", "desc": "Synthesizing all agent reports"},
}

PARALLEL_AGENTS = [
    "recent_analyst", "history_analyst", "team_reporter",
    "odds_analyst", "strategy_analyst",
]

STATUS_EMOJI = {
    "waiting": ":gray[Waiting]",
    "running": ":blue[Running...]",
    "success": ":green[Done]",
    "fallback": ":orange[Fallback]",
    "failed": ":red[Failed]",
}


@st.cache_data(ttl=600)
def fetch_nba_schedule(date_str: str):
    """Fetch NBA schedule for a given date from ESPN API."""
    try:
        formatted = date_str.replace("-", "")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={formatted}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            games = []
            for event in data.get("events", []):
                competition = event["competitions"][0]
                competitors = competition["competitors"]
                home_team = next(t["team"]["displayName"] for t in competitors if t["homeAway"] == "home")
                away_team = next(t["team"]["displayName"] for t in competitors if t["homeAway"] == "away")
                games.append({"home": home_team, "away": away_team})
            return games
    except Exception:
        pass
    return []


def render_agent_status_native(container, agent_states: dict):
    """Render agent status using Streamlit native components."""
    all_agents = PARALLEL_AGENTS + ["final_predictor"]
    for agent_key in all_agents:
        meta = AGENT_META[agent_key]
        state = agent_states.get(agent_key, "waiting")
        status_text = STATUS_EMOJI.get(state, f":gray[{state}]")
        container.markdown(
            f"**Agent {meta['icon']}** | {meta['name']} — _{meta['desc']}_ | {status_text}"
        )


def display_results(details: dict, exec_time: float):
    """Display prediction results with styled cards."""
    winner = details.get("winner", "Unknown")
    probability = details.get("win_probability", 0)
    score = details.get("score_prediction", "N/A")
    confidence = details.get("confidence_level", "N/A")

    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="result-card-winner">
            <div class="result-label">Predicted Winner</div>
            <div class="result-value-green">{winner}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="result-card">
            <div class="result-label">Win Probability</div>
            <div class="result-value-orange">{probability}%</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="result-card">
            <div class="result-label">Confidence</div>
            <div class="result-value">{confidence}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    sc1, sc2 = st.columns([1, 2])
    with sc1:
        st.markdown(f"""<div class="result-card">
            <div class="result-label">Predicted Score</div>
            <div class="result-value" style="font-size:1.3rem;">{score}</div>
        </div>""", unsafe_allow_html=True)
    with sc2:
        agreement = details.get("agent_agreement", "N/A")
        risk = details.get("risk_warning", "None")
        st.markdown(f"""<div class="result-card">
            <div class="result-label">Agent Agreement</div>
            <div class="result-value" style="font-size:1.3rem;">{agreement}</div>
            <div style="color:#ef4444;font-size:0.85rem;margin-top:8px;">{risk}</div>
        </div>""", unsafe_allow_html=True)

    summary = details.get("summary", "No summary provided.")
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

    factors = details.get("key_factors", [])
    if factors:
        st.markdown("**Key Factors**")
        chips_html = "".join(f'<span class="factor-chip">{f}</span>' for f in factors)
        st.markdown(f'<div style="margin-bottom:16px;">{chips_html}</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="text-align:center;color:#4b5563;font-size:0.8rem;margin-top:12px;">'
        f'Execution time: {exec_time:.1f}s | 6 agents (5 parallel + 1 synthesis)</div>',
        unsafe_allow_html=True,
    )


def run_prediction_stream(home_team: str, away_team: str):
    """Run prediction with SSE streaming for live agent status updates."""
    agent_states = {a: "waiting" for a in PARALLEL_AGENTS}
    agent_states["final_predictor"] = "waiting"

    # Use st.status for the agent tracker (Streamlit native, renders properly)
    status_container = st.status("Agent Pipeline Running...", expanded=True)
    tracker_placeholder = status_container.empty()
    render_agent_status_native(tracker_placeholder, agent_states)

    payload = {"team_home": home_team, "team_away": away_team}
    start_ts = time.time()

    try:
        response = requests.post(STREAM_URL, json=payload, stream=True, timeout=300)
    except requests.exceptions.ConnectionError:
        status_container.update(label="Connection Failed", state="error", expanded=True)
        st.error(
            "Cannot connect to the backend server. "
            "Make sure FastAPI is running:\n\n"
            "```\npython -m uvicorn app.main:app --port 8000\n```"
        )
        return
    except requests.exceptions.Timeout:
        status_container.update(label="Timeout", state="error", expanded=True)
        st.error("The prediction timed out. Please try again.")
        return

    if response.status_code != 200:
        status_container.update(label="Backend Error", state="error", expanded=True)
        st.error(f"Backend error ({response.status_code})")
        return

    prediction_data = None

    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        try:
            event = json.loads(line[6:])
        except json.JSONDecodeError:
            continue

        event_type = event.get("type")

        if event_type == "agent_start":
            agent_key = event.get("agent")
            if agent_key in agent_states:
                agent_states[agent_key] = "running"
            tracker_placeholder.empty()
            render_agent_status_native(tracker_placeholder, agent_states)

        elif event_type == "agent_done":
            agent_key = event.get("agent")
            status = event.get("status", "success")
            if agent_key in agent_states:
                agent_states[agent_key] = status
            parallel_done = all(
                agent_states.get(a) not in ("waiting", "running")
                for a in PARALLEL_AGENTS
            )
            if parallel_done and agent_key != "final_predictor":
                agent_states["final_predictor"] = "running"
            tracker_placeholder.empty()
            render_agent_status_native(tracker_placeholder, agent_states)

        elif event_type == "result":
            prediction_data = event

        elif event_type == "error":
            status_container.update(label="Pipeline Error", state="error", expanded=True)
            st.error(f"Pipeline error: {event.get('message')}")
            return

    elapsed = time.time() - start_ts

    if not prediction_data:
        status_container.update(label="No Result", state="error", expanded=True)
        st.error("No prediction received from the backend.")
        return

    # Final update - all done
    for a in agent_states:
        if agent_states[a] == "running":
            agent_states[a] = "success"
    tracker_placeholder.empty()
    render_agent_status_native(tracker_placeholder, agent_states)
    status_container.update(label="All Agents Complete!", state="complete", expanded=False)

    display_results(
        prediction_data.get("prediction_details", {}),
        prediction_data.get("execution_time_seconds", elapsed),
    )


def run_prediction_fallback(home_team: str, away_team: str):
    """Fallback: non-streaming prediction."""
    agent_states = {a: "running" for a in PARALLEL_AGENTS}
    agent_states["final_predictor"] = "waiting"

    status_container = st.status("Running prediction...", expanded=True)
    tracker_placeholder = status_container.empty()
    render_agent_status_native(tracker_placeholder, agent_states)

    payload = {"team_home": home_team, "team_away": away_team}
    start_ts = time.time()

    try:
        response = requests.post(API_URL, json=payload, timeout=300)
    except requests.exceptions.ConnectionError:
        status_container.update(label="Connection Failed", state="error", expanded=True)
        st.error(
            "Cannot connect to the backend server. "
            "Make sure FastAPI is running:\n\n"
            "```\npython -m uvicorn app.main:app --port 8000\n```"
        )
        return
    except requests.exceptions.Timeout:
        status_container.update(label="Timeout", state="error", expanded=True)
        st.error("The prediction timed out. Please try again.")
        return

    elapsed = time.time() - start_ts

    if response.status_code != 200:
        status_container.update(label="Backend Error", state="error", expanded=True)
        st.error(f"Backend error ({response.status_code}): {response.text}")
        return

    data = response.json()
    agent_status = data.get("agent_status", {})
    for a in PARALLEL_AGENTS + ["final_predictor"]:
        agent_states[a] = agent_status.get(a, "success")
    tracker_placeholder.empty()
    render_agent_status_native(tracker_placeholder, agent_states)
    status_container.update(label="All Agents Complete!", state="complete", expanded=False)

    display_results(data.get("prediction_details", {}), elapsed)


def main():
    st.markdown('<div class="hero-title">NBA Game Predictor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Multi-Agent AI System with RAG | 6 Specialized Agents | Real-time Tracking</div>',
        unsafe_allow_html=True,
    )

    col_date, col_spacer = st.columns([1, 2])
    with col_date:
        selected_date = st.date_input(
            "Select Game Date",
            value=datetime.now().date(),
            min_value=datetime.now().date() - timedelta(days=7),
            max_value=datetime.now().date() + timedelta(days=7),
        )

    date_str = selected_date.strftime("%Y-%m-%d")

    with st.spinner("Loading NBA schedule..."):
        games = fetch_nba_schedule(date_str)

    if not games:
        st.info(f"No games found for {date_str}. Pick another date or enter teams manually below.")
        st.markdown("### Manual Input")
        mc1, mc2 = st.columns(2)
        with mc1:
            manual_home = st.text_input("Home Team", placeholder="e.g. Los Angeles Lakers")
        with mc2:
            manual_away = st.text_input("Away Team", placeholder="e.g. Boston Celtics")

        if st.button("Get AI Prediction", type="primary", use_container_width=True,
                      disabled=not (manual_home and manual_away)):
            try:
                run_prediction_stream(manual_home.strip(), manual_away.strip())
            except Exception:
                run_prediction_fallback(manual_home.strip(), manual_away.strip())
        return

    st.markdown(f"**{len(games)} games on {date_str}**")

    options = [f"{g['away']}  @  {g['home']}" for g in games]
    selected_idx = st.selectbox(
        "Choose a game", range(len(options)),
        format_func=lambda i: options[i], label_visibility="collapsed",
    )
    selected_game = games[selected_idx]

    st.markdown(f"""<div class="game-card">
        <div class="team-label">AWAY</div>
        <div class="team-name">{selected_game['away']}</div>
        <div class="vs-text">VS</div>
        <div class="team-name">{selected_game['home']}</div>
        <div class="team-label">HOME</div>
    </div>""", unsafe_allow_html=True)

    if st.button("Get AI Prediction", type="primary", use_container_width=True):
        try:
            run_prediction_stream(selected_game["home"], selected_game["away"])
        except Exception:
            run_prediction_fallback(selected_game["home"], selected_game["away"])

    st.markdown(
        '<div class="footer">Powered by LangGraph Multi-Agent System | FAISS RAG | Parallel Fan-out Architecture</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
