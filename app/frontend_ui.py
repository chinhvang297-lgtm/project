"""
NBA Game Predictor - Streamlit Frontend

Features:
- Date picker with ESPN game schedule
- Live agent status tracking via SSE streaming
- Beautiful dark theme with animated progress indicators
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

st.markdown("""
<style>
    /* ─── Global ─── */
    .main { background-color: #0e1117; }
    .block-container { max-width: 960px; padding-top: 2rem; }

    /* ─── Header ─── */
    .hero-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f97316, #ef4444);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        text-align: center;
        color: #9ca3af;
        font-size: 1.05rem;
        margin-bottom: 2.5rem;
    }

    /* ─── Game Card ─── */
    .game-card {
        background: linear-gradient(145deg, #1e293b, #1a1f2e);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 20px;
        transition: border-color 0.2s;
    }
    .game-card:hover { border-color: #f97316; }
    .vs-text {
        text-align: center;
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 700;
        letter-spacing: 3px;
    }
    .team-name {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f1f5f9;
        text-align: center;
        padding: 6px 0;
    }
    .team-label {
        text-align: center;
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* ─── Agent Tracker ─── */
    .agent-tracker {
        background: linear-gradient(145deg, #1e293b, #1a1f2e);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px 28px;
        margin: 16px 0;
    }
    .agent-tracker-title {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 16px;
        font-weight: 600;
    }
    .agent-row {
        display: flex;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #1f2937;
    }
    .agent-row:last-child { border-bottom: none; }
    .agent-icon {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 700;
        margin-right: 14px;
        flex-shrink: 0;
    }
    .agent-icon-waiting {
        background: #1f2937;
        color: #4b5563;
        border: 1px solid #374151;
    }
    .agent-icon-running {
        background: #1e3a5f;
        color: #60a5fa;
        border: 1px solid #3b82f6;
        animation: pulse 1.5s ease-in-out infinite;
    }
    .agent-icon-done {
        background: #064e3b;
        color: #34d399;
        border: 1px solid #10b981;
    }
    .agent-icon-fail {
        background: #7f1d1d;
        color: #fca5a5;
        border: 1px solid #ef4444;
    }
    .agent-info { flex: 1; }
    .agent-name {
        font-size: 0.95rem;
        font-weight: 600;
        color: #e2e8f0;
    }
    .agent-desc {
        font-size: 0.78rem;
        color: #64748b;
    }
    .agent-badge {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .badge-waiting { background: #1f2937; color: #4b5563; }
    .badge-running { background: #1e3a5f; color: #60a5fa; }
    .badge-done { background: #064e3b; color: #34d399; }
    .badge-fail { background: #7f1d1d; color: #fca5a5; }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* ─── Result Cards ─── */
    .result-card {
        background: linear-gradient(145deg, #1e293b, #1a1f2e);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
    }
    .result-card-winner {
        background: linear-gradient(145deg, #1a2e1a, #1e293b);
        border: 1px solid #22c55e;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
    }
    .result-label {
        font-size: 0.8rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 4px;
    }
    .result-value {
        font-size: 2rem;
        font-weight: 800;
        color: #f1f5f9;
    }
    .result-value-green {
        font-size: 2rem;
        font-weight: 800;
        color: #22c55e;
    }
    .result-value-orange {
        font-size: 2rem;
        font-weight: 800;
        color: #f97316;
    }

    /* ─── Summary Box ─── */
    .summary-box {
        background: linear-gradient(145deg, #1e293b, #1a1f2e);
        border-left: 4px solid #f97316;
        border-radius: 0 12px 12px 0;
        padding: 20px 24px;
        margin: 16px 0;
        color: #e2e8f0;
        font-size: 1.05rem;
        line-height: 1.7;
    }

    /* ─── Factor Chips ─── */
    .factor-chip {
        display: inline-block;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px 14px;
        margin: 4px;
        color: #e2e8f0;
        font-size: 0.9rem;
    }

    /* ─── Footer ─── */
    .footer {
        text-align: center;
        color: #4b5563;
        font-size: 0.8rem;
        margin-top: 60px;
        padding: 20px 0;
        border-top: 1px solid #1f2937;
    }

    /* hide default streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/api/v1/predict"
STREAM_URL = "http://127.0.0.1:8000/api/v1/predict/stream"

AGENT_META = {
    "recent_analyst": {"num": "1", "name": "Recent Stats Analyst", "desc": "Analyzing recent game performance"},
    "history_analyst": {"num": "2", "name": "Historical Matchup (RAG)", "desc": "Searching vector database + web"},
    "team_reporter": {"num": "3", "name": "News & Injury Reporter", "desc": "Scanning injury reports & news"},
    "odds_analyst": {"num": "4", "name": "Betting Odds Analyst", "desc": "Evaluating market odds & spreads"},
    "strategy_analyst": {"num": "5", "name": "Tactical Strategy Analyst", "desc": "Analyzing tactical matchups"},
    "final_predictor": {"num": "6", "name": "Final Predictor", "desc": "Synthesizing all agent reports"},
}

PARALLEL_AGENTS = [
    "recent_analyst", "history_analyst", "team_reporter",
    "odds_analyst", "strategy_analyst",
]


@st.cache_data(ttl=600)
def fetch_nba_schedule(date_str: str):
    """Fetch NBA schedule for a given date from ESPN API."""
    try:
        formatted = date_str.replace("-", "")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={formatted}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            games = []
            for event in data.get("events", []):
                competition = event["competitions"][0]
                competitors = competition["competitors"]
                home_team = next(
                    t["team"]["displayName"]
                    for t in competitors
                    if t["homeAway"] == "home"
                )
                away_team = next(
                    t["team"]["displayName"]
                    for t in competitors
                    if t["homeAway"] == "away"
                )
                games.append({"home": home_team, "away": away_team})
            return games
    except Exception:
        pass
    return []


def render_agent_tracker(agent_states: dict) -> str:
    """Generate HTML for the agent status tracker panel."""
    all_agents = PARALLEL_AGENTS + ["final_predictor"]
    rows = []
    for agent_key in all_agents:
        meta = AGENT_META[agent_key]
        state = agent_states.get(agent_key, "waiting")

        if state == "waiting":
            icon_cls, badge_cls, badge_text = "agent-icon-waiting", "badge-waiting", "Waiting"
        elif state == "running":
            icon_cls, badge_cls, badge_text = "agent-icon-running", "badge-running", "Running"
        elif state in ("success", "fallback"):
            icon_cls, badge_cls, badge_text = "agent-icon-done", "badge-done", "Done"
        else:
            icon_cls, badge_cls, badge_text = "agent-icon-fail", "badge-fail", "Failed"

        rows.append(f"""
        <div class="agent-row">
            <div class="agent-icon {icon_cls}">{meta['num']}</div>
            <div class="agent-info">
                <div class="agent-name">{meta['name']}</div>
                <div class="agent-desc">{meta['desc']}</div>
            </div>
            <span class="agent-badge {badge_cls}">{badge_text}</span>
        </div>
        """)

    return f"""
    <div class="agent-tracker">
        <div class="agent-tracker-title">Agent Pipeline Status</div>
        {''.join(rows)}
    </div>
    """


def run_prediction_stream(home_team: str, away_team: str):
    """Run prediction with SSE streaming for live agent status updates."""
    tracker_placeholder = st.empty()
    result_placeholder = st.empty()

    # Initialize all agents as "waiting"
    agent_states = {a: "waiting" for a in PARALLEL_AGENTS}
    agent_states["final_predictor"] = "waiting"

    # Show initial tracker
    tracker_placeholder.markdown(
        render_agent_tracker(agent_states), unsafe_allow_html=True
    )

    payload = {"team_home": home_team, "team_away": away_team}
    start_ts = time.time()

    try:
        response = requests.post(
            STREAM_URL, json=payload, stream=True, timeout=300
        )
    except requests.exceptions.ConnectionError:
        st.error(
            "Cannot connect to the backend server. "
            "Make sure FastAPI is running:\n\n"
            "```\npython -m uvicorn app.main:app --port 8000\n```"
        )
        return
    except requests.exceptions.Timeout:
        st.error("The prediction timed out. Please try again.")
        return

    if response.status_code != 200:
        st.error(f"Backend error ({response.status_code})")
        return

    prediction_data = None

    # Process SSE stream
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
            tracker_placeholder.markdown(
                render_agent_tracker(agent_states), unsafe_allow_html=True
            )

        elif event_type == "agent_done":
            agent_key = event.get("agent")
            status = event.get("status", "success")
            if agent_key in agent_states:
                agent_states[agent_key] = status
            # If all parallel agents done, mark final_predictor as running
            parallel_done = all(
                agent_states.get(a) not in ("waiting", "running")
                for a in PARALLEL_AGENTS
            )
            if parallel_done and agent_key != "final_predictor":
                agent_states["final_predictor"] = "running"
            tracker_placeholder.markdown(
                render_agent_tracker(agent_states), unsafe_allow_html=True
            )

        elif event_type == "result":
            prediction_data = event

        elif event_type == "error":
            st.error(f"Pipeline error: {event.get('message')}")
            return

    elapsed = time.time() - start_ts

    if not prediction_data:
        st.error("No prediction received from the backend.")
        return

    # Final tracker update - all done
    for a in agent_states:
        if agent_states[a] == "running":
            agent_states[a] = "success"
    tracker_placeholder.markdown(
        render_agent_tracker(agent_states), unsafe_allow_html=True
    )

    # ─── Display Results ───
    details = prediction_data.get("prediction_details", {})

    winner = details.get("winner", "Unknown")
    probability = details.get("win_probability", 0)
    score = details.get("score_prediction", "N/A")
    confidence = details.get("confidence_level", "N/A")

    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="result-card-winner">
            <div class="result-label">Predicted Winner</div>
            <div class="result-value-green">{winner}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">Win Probability</div>
            <div class="result-value-orange">{probability}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">Confidence</div>
            <div class="result-value">{confidence}</div>
        </div>
        """, unsafe_allow_html=True)

    # Score + Agreement
    st.markdown("")
    sc1, sc2 = st.columns([1, 2])
    with sc1:
        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">Predicted Score</div>
            <div class="result-value" style="font-size:1.3rem;">{score}</div>
        </div>
        """, unsafe_allow_html=True)
    with sc2:
        agreement = details.get("agent_agreement", "N/A")
        risk = details.get("risk_warning", "None")
        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">Agent Agreement</div>
            <div class="result-value" style="font-size:1.3rem;">{agreement}</div>
            <div style="color:#ef4444;font-size:0.85rem;margin-top:8px;">{risk}</div>
        </div>
        """, unsafe_allow_html=True)

    # Summary
    summary = details.get("summary", "No summary provided.")
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

    # Key Factors
    factors = details.get("key_factors", [])
    if factors:
        st.markdown("**Key Factors**")
        chips_html = "".join(f'<span class="factor-chip">{f}</span>' for f in factors)
        st.markdown(
            f'<div style="margin-bottom:16px;">{chips_html}</div>',
            unsafe_allow_html=True,
        )

    # Execution time
    exec_time = prediction_data.get("execution_time_seconds", elapsed)
    st.markdown(
        f'<div style="text-align:center;color:#4b5563;font-size:0.8rem;margin-top:12px;">'
        f'Execution time: {exec_time:.1f}s | 6 agents (5 parallel + 1 synthesis)</div>',
        unsafe_allow_html=True,
    )


def run_prediction_fallback(home_team: str, away_team: str):
    """Fallback: non-streaming prediction (if SSE fails, use regular endpoint)."""
    tracker_placeholder = st.empty()

    # Show all agents as running
    agent_states = {a: "running" for a in PARALLEL_AGENTS}
    agent_states["final_predictor"] = "waiting"
    tracker_placeholder.markdown(
        render_agent_tracker(agent_states), unsafe_allow_html=True
    )

    payload = {"team_home": home_team, "team_away": away_team}
    start_ts = time.time()

    try:
        response = requests.post(API_URL, json=payload, timeout=300)
    except requests.exceptions.ConnectionError:
        st.error(
            "Cannot connect to the backend server. "
            "Make sure FastAPI is running:\n\n"
            "```\npython -m uvicorn app.main:app --port 8000\n```"
        )
        return
    except requests.exceptions.Timeout:
        st.error("The prediction timed out. Please try again.")
        return

    elapsed = time.time() - start_ts

    if response.status_code != 200:
        st.error(f"Backend error ({response.status_code}): {response.text}")
        return

    data = response.json()
    agent_status = data.get("agent_status", {})

    # Update tracker with actual results
    for a in PARALLEL_AGENTS + ["final_predictor"]:
        agent_states[a] = agent_status.get(a, "success")
    tracker_placeholder.markdown(
        render_agent_tracker(agent_states), unsafe_allow_html=True
    )

    details = data.get("prediction_details", {})
    winner = details.get("winner", "Unknown")
    probability = details.get("win_probability", 0)
    score = details.get("score_prediction", "N/A")
    confidence = details.get("confidence_level", "N/A")

    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="result-card-winner">
            <div class="result-label">Predicted Winner</div>
            <div class="result-value-green">{winner}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">Win Probability</div>
            <div class="result-value-orange">{probability}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">Confidence</div>
            <div class="result-value">{confidence}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    sc1, sc2 = st.columns([1, 2])
    with sc1:
        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">Predicted Score</div>
            <div class="result-value" style="font-size:1.3rem;">{score}</div>
        </div>
        """, unsafe_allow_html=True)
    with sc2:
        agreement = details.get("agent_agreement", "N/A")
        risk = details.get("risk_warning", "None")
        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">Agent Agreement</div>
            <div class="result-value" style="font-size:1.3rem;">{agreement}</div>
            <div style="color:#ef4444;font-size:0.85rem;margin-top:8px;">{risk}</div>
        </div>
        """, unsafe_allow_html=True)

    summary = details.get("summary", "No summary provided.")
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

    factors = details.get("key_factors", [])
    if factors:
        st.markdown("**Key Factors**")
        chips_html = "".join(f'<span class="factor-chip">{f}</span>' for f in factors)
        st.markdown(
            f'<div style="margin-bottom:16px;">{chips_html}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="text-align:center;color:#4b5563;font-size:0.8rem;margin-top:12px;">'
        f'Execution time: {elapsed:.1f}s | 6 agents (5 parallel + 1 synthesis)</div>',
        unsafe_allow_html=True,
    )


def main():
    # ─── Header ───
    st.markdown('<div class="hero-title">NBA Game Predictor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Multi-Agent AI System with RAG &bull; 6 Specialized Agents &bull; Real-time Tracking</div>',
        unsafe_allow_html=True,
    )

    # ─── Date Picker ───
    col_date, col_spacer = st.columns([1, 2])
    with col_date:
        selected_date = st.date_input(
            "Select Game Date",
            value=datetime.now().date(),
            min_value=datetime.now().date() - timedelta(days=7),
            max_value=datetime.now().date() + timedelta(days=7),
        )

    date_str = selected_date.strftime("%Y-%m-%d")

    # ─── Fetch Games ───
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

        if st.button(
            "Get AI Prediction",
            type="primary",
            use_container_width=True,
            disabled=not (manual_home and manual_away),
        ):
            try:
                run_prediction_stream(manual_home.strip(), manual_away.strip())
            except Exception:
                run_prediction_fallback(manual_home.strip(), manual_away.strip())
        return

    # ─── Game Selection ───
    st.markdown(f"**{len(games)} games on {date_str}**")

    options = [f"{g['away']}  @  {g['home']}" for g in games]
    selected_idx = st.selectbox(
        "Choose a game",
        range(len(options)),
        format_func=lambda i: options[i],
        label_visibility="collapsed",
    )
    selected_game = games[selected_idx]

    # ─── Game Card Preview ───
    st.markdown(f"""
    <div class="game-card">
        <div class="team-label">AWAY</div>
        <div class="team-name">{selected_game['away']}</div>
        <div class="vs-text">VS</div>
        <div class="team-name">{selected_game['home']}</div>
        <div class="team-label">HOME</div>
    </div>
    """, unsafe_allow_html=True)

    # ─── Predict Button ───
    if st.button("Get AI Prediction", type="primary", use_container_width=True):
        try:
            run_prediction_stream(selected_game["home"], selected_game["away"])
        except Exception:
            run_prediction_fallback(selected_game["home"], selected_game["away"])

    # ─── Footer ───
    st.markdown(
        '<div class="footer">Powered by LangGraph Multi-Agent System &bull; '
        'FAISS RAG &bull; Parallel Fan-out Architecture</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
