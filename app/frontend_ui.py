import streamlit as st
import requests
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
    .block-container { max-width: 900px; padding-top: 2rem; }

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

    /* ─── Factors ─── */
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

    /* ─── Agent Status ─── */
    .agent-bar {
        display: flex;
        gap: 8px;
        justify-content: center;
        flex-wrap: wrap;
        margin: 12px 0;
    }
    .agent-dot-ok {
        background: #065f46;
        color: #34d399;
        border-radius: 20px;
        padding: 5px 14px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .agent-dot-fail {
        background: #7f1d1d;
        color: #fca5a5;
        border-radius: 20px;
        padding: 5px 14px;
        font-size: 0.78rem;
        font-weight: 600;
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

    /* hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/api/v1/predict"


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
                games.append({
                    "home": home_team,
                    "away": away_team,
                })
            return games
    except Exception:
        pass
    return []


def main():
    # ─── Header ───
    st.markdown('<div class="hero-title">NBA Game Predictor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">AI-powered predictions using 6 specialized agents</div>',
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
            "Predict",
            type="primary",
            use_container_width=True,
            disabled=not (manual_home and manual_away),
        ):
            run_prediction(manual_home.strip(), manual_away.strip())
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
        run_prediction(selected_game["home"], selected_game["away"])

    # ─── Footer ───
    st.markdown(
        '<div class="footer">Powered by LangGraph Multi-Agent System</div>',
        unsafe_allow_html=True,
    )


def run_prediction(home_team: str, away_team: str):
    """Execute prediction and display results."""
    status = st.status("Running AI Prediction Pipeline...", expanded=True)

    status.write("Connecting to backend...")
    agent_names = [
        "Agent 1: Recent Stats",
        "Agent 2: History (RAG)",
        "Agent 3: News & Injuries",
        "Agent 4: Betting Odds",
        "Agent 5: Tactical Matchups",
    ]
    for name in agent_names:
        status.write(f"Running {name}...")

    status.write("Agent 6: Synthesizing final prediction...")

    payload = {"team_home": home_team, "team_away": away_team}
    start_ts = time.time()

    try:
        response = requests.post(API_URL, json=payload, timeout=180)
    except requests.exceptions.ConnectionError:
        status.update(label="Connection Failed", state="error")
        st.error(
            "Cannot connect to the backend server. "
            "Make sure FastAPI is running:\n\n"
            "```\npython -m uvicorn app.main:app --port 8000\n```"
        )
        return
    except requests.exceptions.Timeout:
        status.update(label="Timeout", state="error")
        st.error("The prediction timed out. Please try again.")
        return

    elapsed = time.time() - start_ts

    if response.status_code != 200:
        status.update(label="Error", state="error")
        st.error(f"Backend error ({response.status_code}): {response.text}")
        return

    data = response.json()
    details = data.get("prediction_details", {})
    agent_status = data.get("agent_status", {})

    status.update(label=f"Prediction Complete ({elapsed:.1f}s)", state="complete", expanded=False)

    # ─── Winner & Probability ───
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

    # ─── Score Prediction ───
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

    # ─── Summary ───
    summary = details.get("summary", "No summary provided.")
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

    # ─── Key Factors ───
    factors = details.get("key_factors", [])
    if factors:
        st.markdown("**Key Factors**")
        chips_html = "".join(f'<span class="factor-chip">{f}</span>' for f in factors)
        st.markdown(
            f'<div style="margin-bottom:16px;">{chips_html}</div>',
            unsafe_allow_html=True,
        )

    # ─── Agent Status ───
    if agent_status:
        st.markdown("**Agent Status**")
        dots = []
        for agent, s in agent_status.items():
            display_name = agent.replace("_", " ").title()
            if s in ("success", "fallback"):
                dots.append(f'<span class="agent-dot-ok">{display_name}</span>')
            else:
                dots.append(f'<span class="agent-dot-fail">{display_name} ({s})</span>')
        st.markdown(
            f'<div class="agent-bar">{"".join(dots)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="text-align:center;color:#4b5563;font-size:0.8rem;margin-top:12px;">'
        f'Execution time: {elapsed:.1f}s</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
