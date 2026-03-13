"""
NBA 比赛预测系统 - Streamlit 前端
Glassmorphism 暗色主题 + 中文界面
"""
import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
from datetime import datetime, timedelta

st.set_page_config(
    page_title="NBA 智能预测系统",
    page_icon="https://cdn-icons-png.flaticon.com/512/889/889442.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── 全局 CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans SC', 'Inter', sans-serif !important;
}
.main .block-container {
    max-width: 900px;
    padding: 2rem 1rem 4rem 1rem;
}
section[data-testid="stSidebar"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }
header[data-testid="stHeader"] { background: transparent; }

.stSelectbox > div > div { border-radius: 12px !important; }
.stDateInput > div > div { border-radius: 12px !important; }
.stTextInput > div > div > input { border-radius: 12px !important; }
button[kind="primary"] {
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.65rem 2rem !important;
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    letter-spacing: 0.5px;
    transition: all 0.3s ease !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #818cf8, #a78bfa) !important;
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4) !important;
    transform: translateY(-1px) !important;
}
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/api/v1/predict"
STREAM_URL = "http://127.0.0.1:8000/api/v1/predict/stream"

AGENT_LIST = [
    ("recent_analyst",   "近期表现分析师",    "分析两队最近5场比赛的状态与势头"),
    ("history_analyst",  "历史对战分析师",    "RAG向量检索 + 网络搜索历史数据"),
    ("team_reporter",    "伤病新闻记者",      "扫描伤病报告与交易新闻"),
    ("odds_analyst",     "赔率市场分析师",    "解读博彩市场赔率与资金流向"),
    ("strategy_analyst", "战术对位分析师",    "分析首发阵容与关键对位"),
    ("final_predictor",  "最终决策合成器",    "综合5份专家报告生成预测"),
]

PARALLEL_AGENTS = [a[0] for a in AGENT_LIST[:5]]


@st.cache_data(ttl=600)
def fetch_nba_schedule(date_str: str):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str.replace('-', '')}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if r.status_code != 200:
            return []
        games = []
        for ev in r.json().get("events", []):
            comp = ev["competitions"][0]["competitors"]
            home = next(t["team"]["displayName"] for t in comp if t["homeAway"] == "home")
            away = next(t["team"]["displayName"] for t in comp if t["homeAway"] == "away")
            games.append({"home": home, "away": away})
        return games
    except Exception:
        return []


def _badge(state: str) -> str:
    m = {
        "waiting":  ("等待中",  "#3b3b4f", "#6b7280"),
        "running":  ("运行中",  "#1e3a5f", "#60a5fa"),
        "success":  ("已完成",  "#064e3b", "#34d399"),
        "fallback": ("已降级",  "#78350f", "#fbbf24"),
        "failed":   ("失败",    "#7f1d1d", "#fca5a5"),
    }
    label, bg, fg = m.get(state, ("未知", "#3b3b4f", "#9ca3af"))
    return f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:10px;font-size:0.75rem;font-weight:600;letter-spacing:0.5px;">{label}</span>'


def _icon(num: int, state: str) -> str:
    colors = {
        "waiting": ("#3b3b4f", "#6b7280", "#4b5563"),
        "running": ("#1e3a5f", "#60a5fa", "#3b82f6"),
        "success": ("#064e3b", "#34d399", "#10b981"),
        "fallback":("#78350f", "#fbbf24", "#d97706"),
        "failed":  ("#7f1d1d", "#fca5a5", "#ef4444"),
    }
    bg, fg, border = colors.get(state, ("#3b3b4f", "#9ca3af", "#4b5563"))
    anim = 'animation:blink 1.2s ease-in-out infinite;' if state == "running" else ''
    return (
        f'<div style="width:30px;height:30px;border-radius:8px;display:inline-flex;'
        f'align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;'
        f'background:{bg};color:{fg};border:1.5px solid {border};flex-shrink:0;{anim}">'
        f'{num}</div>'
    )


def render_tracker_html(agent_states: dict) -> str:
    rows = ""
    for i, (key, name, desc) in enumerate(AGENT_LIST, 1):
        state = agent_states.get(key, "waiting")
        rows += f"""
        <div style="display:flex;align-items:center;gap:14px;padding:9px 0;
                     border-bottom:1px solid rgba(255,255,255,0.04);">
            {_icon(i, state)}
            <div style="flex:1;min-width:0;">
                <div style="font-size:0.9rem;font-weight:600;color:#e2e8f0;">{name}</div>
                <div style="font-size:0.75rem;color:#64748b;">{desc}</div>
            </div>
            {_badge(state)}
        </div>"""

    return f"""
    <div style="background:rgba(30,41,59,0.65);backdrop-filter:blur(12px);
                border:1px solid rgba(255,255,255,0.07);border-radius:16px;
                padding:20px 24px;margin:8px 0;font-family:'Noto Sans SC','Inter',sans-serif;">
        <div style="font-size:0.78rem;color:#64748b;text-transform:uppercase;
                     letter-spacing:2px;font-weight:600;margin-bottom:12px;">
            Agent 执行状态
        </div>
        {rows}
    </div>
    <style>@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0.4}}}}</style>
    """


def display_results(details: dict, exec_time: float):
    winner = details.get("winner", "未知")
    prob = details.get("win_probability", 0)
    score = details.get("score_prediction", "N/A")
    confidence = details.get("confidence_level", "N/A")
    agreement = details.get("agent_agreement", "N/A")
    risk = details.get("risk_warning", "")
    summary = details.get("summary", "")
    factors = details.get("key_factors", [])

    st.markdown("")

    # 冠军横幅
    components.html(f"""
    <div style="background:linear-gradient(135deg,rgba(16,185,129,0.12),rgba(99,102,241,0.10));
                border:1px solid rgba(16,185,129,0.25);border-radius:20px;
                padding:32px 24px;text-align:center;font-family:'Noto Sans SC','Inter',sans-serif;">
        <div style="font-size:0.75rem;color:#9ca3af;text-transform:uppercase;
                     letter-spacing:3px;font-weight:600;">预测获胜方</div>
        <div style="font-size:2.4rem;font-weight:800;color:#34d399;margin:6px 0 2px;">
            {winner}
        </div>
        <div style="font-size:1.1rem;color:#a78bfa;font-weight:600;">胜率 {prob}%</div>
    </div>
    """, height=150)

    # 统计卡片
    stats = [
        ("比分预测", score, "#e2e8f0"),
        ("置信度", confidence, "#fbbf24"),
        ("Agent共识", agreement, "#818cf8"),
    ]
    cards_html = ""
    for label, value, color in stats:
        cards_html += f"""
        <div style="flex:1;background:rgba(30,41,59,0.6);backdrop-filter:blur(10px);
                     border:1px solid rgba(255,255,255,0.06);border-radius:16px;
                     padding:20px 16px;text-align:center;">
            <div style="font-size:0.7rem;color:#9ca3af;letter-spacing:2px;
                         font-weight:600;margin-bottom:6px;">{label}</div>
            <div style="font-size:1.35rem;font-weight:700;color:{color};">{value}</div>
        </div>"""

    components.html(f"""
    <div style="display:flex;gap:12px;font-family:'Noto Sans SC','Inter',sans-serif;">
        {cards_html}
    </div>
    """, height=110)

    # 风险警告
    if risk and risk.lower() not in ("none", "n/a", "无", ""):
        st.warning(f"风险提示：{risk}")

    # 综合分析
    if summary:
        components.html(f"""
        <div style="background:rgba(30,41,59,0.5);backdrop-filter:blur(8px);
                     border-left:4px solid #8b5cf6;border-radius:0 14px 14px 0;
                     padding:20px 24px;margin:4px 0;font-family:'Noto Sans SC','Inter',sans-serif;
                     color:#cbd5e1;font-size:0.95rem;line-height:1.85;">
            {summary}
        </div>
        """, height=max(100, len(summary) // 2 + 40))

    # 关键因素
    if factors:
        chips = ""
        for f in factors:
            chips += (
                f'<span style="display:inline-block;background:rgba(99,102,241,0.12);'
                f'border:1px solid rgba(99,102,241,0.25);border-radius:10px;'
                f'padding:6px 14px;margin:4px;color:#a5b4fc;font-size:0.85rem;'
                f'font-weight:500;">{f}</span>'
            )
        components.html(f"""
        <div style="font-family:'Noto Sans SC','Inter',sans-serif;">
            <div style="font-size:0.78rem;color:#64748b;letter-spacing:2px;
                         font-weight:600;margin-bottom:8px;">
                关键因素
            </div>
            <div>{chips}</div>
        </div>
        """, height=max(60, 40 + 36 * ((len(factors) + 2) // 3)))

    st.caption(f"执行耗时 {exec_time:.1f} 秒  |  6个Agent（5个并行 + 1个综合）")


# ─── 预测执行 ───

def run_prediction_stream(home_team: str, away_team: str):
    agent_states = {a: "waiting" for a in PARALLEL_AGENTS}
    agent_states["final_predictor"] = "waiting"

    tracker = st.empty()
    tracker.markdown(render_tracker_html(agent_states), unsafe_allow_html=True)

    try:
        resp = requests.post(STREAM_URL, json={"team_home": home_team, "team_away": away_team},
                             stream=True, timeout=300)
    except requests.exceptions.ConnectionError:
        st.error("无法连接后端服务，请确保 FastAPI 正在运行：\n\n`python -m uvicorn app.main:app --port 8000`")
        return
    except requests.exceptions.Timeout:
        st.error("请求超时，请重试。")
        return

    if resp.status_code != 200:
        st.error(f"后端错误（{resp.status_code}）")
        return

    prediction_data = None
    start_ts = time.time()

    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        try:
            event = json.loads(line[6:])
        except json.JSONDecodeError:
            continue

        etype = event.get("type")
        if etype == "agent_start":
            k = event.get("agent")
            if k in agent_states:
                agent_states[k] = "running"
            tracker.markdown(render_tracker_html(agent_states), unsafe_allow_html=True)

        elif etype == "agent_done":
            k = event.get("agent")
            if k in agent_states:
                agent_states[k] = event.get("status", "success")
            if all(agent_states.get(a) not in ("waiting", "running") for a in PARALLEL_AGENTS):
                if k != "final_predictor":
                    agent_states["final_predictor"] = "running"
            tracker.markdown(render_tracker_html(agent_states), unsafe_allow_html=True)

        elif etype == "result":
            prediction_data = event

        elif etype == "error":
            st.error(f"流水线错误：{event.get('message')}")
            return

    if not prediction_data:
        st.error("未收到预测结果。")
        return

    for a in agent_states:
        if agent_states[a] == "running":
            agent_states[a] = "success"
    tracker.markdown(render_tracker_html(agent_states), unsafe_allow_html=True)

    elapsed = time.time() - start_ts
    display_results(prediction_data.get("prediction_details", {}),
                    prediction_data.get("execution_time_seconds", elapsed))


def run_prediction_fallback(home_team: str, away_team: str):
    agent_states = {a: "running" for a in PARALLEL_AGENTS}
    agent_states["final_predictor"] = "waiting"

    tracker = st.empty()
    tracker.markdown(render_tracker_html(agent_states), unsafe_allow_html=True)

    start_ts = time.time()
    try:
        resp = requests.post(API_URL, json={"team_home": home_team, "team_away": away_team}, timeout=300)
    except requests.exceptions.ConnectionError:
        st.error("无法连接后端服务，请确保 FastAPI 正在运行：\n\n`python -m uvicorn app.main:app --port 8000`")
        return
    except requests.exceptions.Timeout:
        st.error("请求超时，请重试。")
        return
    elapsed = time.time() - start_ts

    if resp.status_code != 200:
        st.error(f"后端错误（{resp.status_code}）：{resp.text}")
        return

    data = resp.json()
    for a in PARALLEL_AGENTS + ["final_predictor"]:
        agent_states[a] = data.get("agent_status", {}).get(a, "success")
    tracker.markdown(render_tracker_html(agent_states), unsafe_allow_html=True)

    display_results(data.get("prediction_details", {}), elapsed)


# ─── 主页面 ───

def main():
    components.html("""
    <div style="text-align:center;font-family:'Noto Sans SC','Inter',sans-serif;padding:10px 0 30px;">
        <div style="font-size:3rem;font-weight:900;
                     background:linear-gradient(135deg,#818cf8,#c084fc,#f472b6);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                     letter-spacing:-1px;line-height:1.1;">
            NBA 智能预测
        </div>
        <div style="color:#64748b;font-size:0.95rem;margin-top:6px;font-weight:400;
                     letter-spacing:0.5px;">
            多Agent协作系统 &nbsp;&bull;&nbsp; FAISS RAG检索增强 &nbsp;&bull;&nbsp; 并行Fan-out架构 &nbsp;&bull;&nbsp; 实时状态追踪
        </div>
    </div>
    """, height=120)

    col_date, _ = st.columns([1, 2])
    with col_date:
        selected_date = st.date_input(
            "选择比赛日期",
            value=datetime.now().date(),
            min_value=datetime.now().date() - timedelta(days=7),
            max_value=datetime.now().date() + timedelta(days=7),
        )
    date_str = selected_date.strftime("%Y-%m-%d")

    with st.spinner("加载赛程中..."):
        games = fetch_nba_schedule(date_str)

    if not games:
        st.info(f"{date_str} 没有比赛，请选择其他日期或手动输入球队：")
        c1, c2 = st.columns(2)
        with c1:
            manual_home = st.text_input("主队", placeholder="例如：Los Angeles Lakers")
        with c2:
            manual_away = st.text_input("客队", placeholder="例如：Boston Celtics")
        if st.button("开始预测", type="primary", use_container_width=True,
                      disabled=not (manual_home and manual_away)):
            try:
                run_prediction_stream(manual_home.strip(), manual_away.strip())
            except Exception:
                run_prediction_fallback(manual_home.strip(), manual_away.strip())
        return

    st.markdown(f"##### {date_str} 共 {len(games)} 场比赛")
    opts = [f"{g['away']}  @  {g['home']}" for g in games]
    idx = st.selectbox("选择比赛", range(len(opts)), format_func=lambda i: opts[i],
                       label_visibility="collapsed")
    game = games[idx]

    components.html(f"""
    <div style="background:linear-gradient(145deg,rgba(30,41,59,0.7),rgba(15,23,42,0.8));
                backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.07);
                border-radius:20px;padding:30px 20px;text-align:center;
                font-family:'Noto Sans SC','Inter',sans-serif;">
        <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;
                     letter-spacing:3px;font-weight:600;">客队</div>
        <div style="font-size:1.6rem;font-weight:800;color:#e2e8f0;margin:4px 0 10px;">
            {game['away']}</div>
        <div style="display:inline-block;background:rgba(99,102,241,0.15);
                     border:1px solid rgba(99,102,241,0.3);border-radius:10px;
                     padding:4px 18px;color:#a5b4fc;font-size:0.85rem;
                     font-weight:700;letter-spacing:3px;">VS</div>
        <div style="font-size:1.6rem;font-weight:800;color:#e2e8f0;margin:10px 0 4px;">
            {game['home']}</div>
        <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;
                     letter-spacing:3px;font-weight:600;">主队</div>
    </div>
    """, height=210)

    if st.button("开始预测", type="primary", use_container_width=True):
        try:
            run_prediction_stream(game["home"], game["away"])
        except Exception:
            run_prediction_fallback(game["home"], game["away"])

    st.markdown("")
    st.markdown("")
    st.caption("基于 LangGraph 多Agent系统  |  FAISS RAG 检索增强  |  Fan-out/Fan-in 并行架构")


if __name__ == "__main__":
    main()
