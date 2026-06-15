import streamlit as st
import pandas as pd
import time
from agent import run_agent, generate_examples

# ── Page Config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Querio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Splash Screen (runs once per session) ────────────────────────
if "splash_done" not in st.session_state:
    st.session_state.splash_done = False

if not st.session_state.splash_done:
    splash = st.empty()
    splash.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
    #MainMenu, footer, header, [data-testid="stSidebar"] { visibility: hidden !important; display: none !important; }
    .splash-wrap {
        position: fixed; inset: 0;
        background: #F5F0FF;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        z-index: 9999;
    }
    .splash-icon {
        font-size: 64px; margin-bottom: 20px;
        animation: floatIcon 1.5s ease-in-out infinite alternate;
        color: #7C3AED;
    }
    @keyframes floatIcon {
        from { transform: translateY(0px); }
        to   { transform: translateY(-12px); }
    }
    .splash-name {
        font-family: 'Space Mono', monospace;
        font-size: 52px; font-weight: 700;
        color: #5B21B6; letter-spacing: -0.02em;
        line-height: 1; margin-bottom: 12px;
    }
    .splash-tagline {
        font-family: 'DM Sans', sans-serif;
        font-size: 15px; color: #7C3AED;
        letter-spacing: 0.10em; text-transform: uppercase;
        margin-bottom: 48px; opacity: 0.65;
    }
    .splash-bar-track {
        width: 220px; height: 3px;
        background: rgba(91,33,182,0.15);
        border-radius: 2px; overflow: hidden;
    }
    .splash-bar-fill {
        height: 100%; width: 0%;
        background: linear-gradient(90deg, #7C3AED, #A78BFA);
        border-radius: 2px;
        animation: loadBar 2.8s ease-out forwards;
    }
    @keyframes loadBar {
        0%   { width: 0%; }
        60%  { width: 75%; }
        85%  { width: 92%; }
        100% { width: 100%; }
    }
    .splash-loading {
        font-family: 'Space Mono', monospace;
        font-size: 11px; color: #7C3AED;
        letter-spacing: 0.18em; text-transform: uppercase;
        margin-top: 18px; opacity: 0.55;
    }
    </style>
    <div class="splash-wrap">
        <div class="splash-icon">◈</div>
        <div class="splash-name">Querio</div>
        <div class="splash-tagline">Query your data with AI</div>
        <div class="splash-bar-track">
            <div class="splash-bar-fill"></div>
        </div>
        <div class="splash-loading">Initializing...</div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(3)
    splash.empty()
    st.session_state.splash_done = True
    st.rerun()

# ── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --accent:        #7C3AED;
    --accent-soft:   #A78BFA;
    --accent-dim:    rgba(124, 58, 237, 0.08);
    --accent-border: rgba(124, 58, 237, 0.25);
    --bg-deep:       #F5F0FF;
    --bg-card:       #FFFFFF;
    --bg-elevated:   #EDE9FE;
    --text-primary:  #1E1B2E;
    --text-secondary:#4C4769;
    --text-muted:    #9490B0;
    --border:        rgba(124,58,237,0.10);
    --border-hover:  rgba(124,58,237,0.22);
    --danger:        #DC2626;
    --mono: 'Space Mono', monospace;
    --sans: 'DM Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--sans) !important;
    background-color: var(--bg-deep) !important;
    color: var(--text-primary) !important;
}

.stApp { background: var(--bg-deep) !important; }

/* ── Remove Streamlit default top padding ── */
.stApp > div:first-child { padding-top: 0 !important; }
[data-testid="stAppViewContainer"] > section:first-child { padding-top: 0 !important; }
[data-testid="stMainBlockContainer"] { padding-top: 1rem !important; }
.block-container { padding-top: 1rem !important; }

/* ── Permanent sidebar ── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1.5px solid rgba(124,58,237,0.14) !important;
    min-width: 270px !important;
    max-width: 270px !important;
    visibility: visible !important;
    display: block !important;
    transform: none !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[kind="headerNoPadding"] {
    display: none !important;
    visibility: hidden !important;
}
[data-testid="stSidebar"] > div { padding-top: 2rem !important; }

/* ── Sidebar brand ── */
.sidebar-brand {
    font-family: var(--mono);
    font-size: 10px; letter-spacing: 0.2em;
    color: var(--accent); text-transform: uppercase;
    padding: 0 1.25rem 1.25rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.sidebar-brand span {
    display: block; font-size: 22px;
    letter-spacing: 0.02em; color: var(--text-primary);
    margin-top: 4px; font-weight: 700;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 1.5px dashed var(--accent-border) !important;
    border-radius: 12px !important;
    background: var(--accent-dim) !important;
    padding: 0.5rem !important;
    transition: all 0.2s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
    background: rgba(124,58,237,0.12) !important;
}

/* ── Alert ── */
[data-testid="stAlert"] {
    background: rgba(124,58,237,0.07) !important;
    border: 1px solid var(--accent-border) !important;
    border-radius: 10px !important;
    color: var(--accent) !important;
}

/* ── Column pills ── */
.col-pill {
    display: inline-block;
    font-family: var(--mono); font-size: 11px;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 6px; padding: 3px 8px;
    margin: 3px 2px; color: var(--text-secondary);
}
.col-pill .dtype { color: var(--accent); margin-left: 4px; }

/* ── Hero ── */
.hero-title {
    font-family: var(--mono); font-size: 11px;
    letter-spacing: 0.25em; color: var(--accent);
    text-transform: uppercase; margin-bottom: 6px;
}
.hero-heading {
    font-size: 40px; font-weight: 600;
    line-height: 1.15; color: var(--text-primary);
    letter-spacing: -0.02em; margin-bottom: 10px;
}
.hero-heading em { font-style: normal; color: var(--accent); }
.hero-sub {
    font-size: 15px; color: var(--text-secondary);
    font-weight: 400; max-width: 520px; line-height: 1.65;
}

.h-divider { height: 1px; background: var(--border); margin: 2rem 0; }

.query-label {
    font-family: var(--mono); font-size: 11px;
    letter-spacing: 0.15em; color: var(--text-muted);
    text-transform: uppercase; margin-bottom: 8px;
}

/* ── Text input ── */
[data-testid="stTextInput"] input {
    background: #FFFFFF !important;
    border: 1.5px solid var(--border-hover) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: var(--sans) !important;
    font-size: 15px !important; padding: 14px 16px !important;
    height: auto !important; transition: all 0.2s ease !important;
    box-shadow: 0 1px 4px rgba(124,58,237,0.05) !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.10) !important;
    outline: none !important;
}
[data-testid="stTextInput"] input::placeholder { color: var(--text-muted) !important; }

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: var(--accent) !important;
    color: #FFFFFF !important; border: none !important;
    border-radius: 10px !important;
    font-family: var(--mono) !important; font-size: 12px !important;
    font-weight: 700 !important; letter-spacing: 0.1em !important;
    padding: 14px 32px !important; text-transform: uppercase !important;
    transition: all 0.2s ease !important; width: 100% !important;
    box-shadow: 0 4px 14px rgba(124,58,237,0.22) !important;
}
[data-testid="stButton"] > button:hover {
    background: #6D28D9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(124,58,237,0.30) !important;
}
[data-testid="stButton"] > button:active { transform: translateY(0px) !important; }

/* ── Answer card ── */
.answer-card {
    background: #FFFFFF;
    border: 1px solid var(--accent-border);
    border-radius: 14px; padding: 1.5rem 1.75rem;
    margin-top: 1rem; position: relative; overflow: hidden;
    box-shadow: 0 2px 12px rgba(124,58,237,0.07);
}
.answer-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent-soft));
}
.answer-label {
    font-family: var(--mono); font-size: 10px;
    letter-spacing: 0.2em; color: var(--accent);
    text-transform: uppercase; margin-bottom: 12px;
    display: flex; align-items: center; gap: 8px;
}
.answer-label::before {
    content: ''; display: inline-block;
    width: 6px; height: 6px;
    background: var(--accent); border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.4; transform:scale(0.75); }
}
.answer-question {
    font-size: 12px; color: var(--text-muted);
    font-family: var(--mono); margin-bottom: 10px;
    padding-bottom: 10px; border-bottom: 1px solid var(--border);
}
.answer-text { font-size: 16px; color: var(--text-primary); line-height: 1.7; }

/* ── Insight card ── */
.insight-card {
    background: #FAF5FF;
    border: 1px solid rgba(124,58,237,0.18);
    border-left: 3px solid var(--accent);
    border-radius: 0 12px 12px 0;
    padding: 1.25rem 1.5rem; margin-top: 12px;
}
.insight-label {
    font-family: var(--mono); font-size: 10px;
    letter-spacing: 0.2em; color: var(--accent);
    text-transform: uppercase; margin-bottom: 10px;
}
.insight-text { font-size: 15px; color: var(--text-secondary); line-height: 1.75; font-style: italic; }

/* ── Error card ── */
.error-card {
    background: #FFF5F5;
    border: 1px solid rgba(220,38,38,0.22);
    border-left: 3px solid var(--danger);
    border-radius: 0 10px 10px 0;
    padding: 14px 16px; margin-top: 8px;
    font-size: 14px; color: var(--danger);
}

/* ── History ── */
.history-item {
    background: var(--bg-elevated); border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 10px;
}
.history-q { font-size: 12px; color: var(--text-muted); font-family: var(--mono); margin-bottom: 6px; }
.history-a { font-size: 14px; color: var(--text-secondary); line-height: 1.6; }

/* ── Empty state ── */
.empty-state { text-align: center; padding: 4rem 2rem; }
.empty-icon  { font-size: 52px; margin-bottom: 1.5rem; color: var(--accent-soft); }
.empty-title { font-size: 22px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.empty-sub   { font-size: 15px; color: var(--text-muted); line-height: 1.6; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(124,58,237,0.05) !important;
}
[data-testid="stExpander"] summary {
    color: var(--text-secondary) !important; font-size: 13px !important;
    font-family: var(--mono) !important; letter-spacing: 0.04em !important;
}

/* ── Stats ── */
.stat-row { display: flex; gap: 10px; margin: 12px 0; }
.stat-box {
    flex: 1; background: var(--accent-dim);
    border: 1px solid var(--accent-border);
    border-radius: 10px; padding: 10px 14px; text-align: center;
}
.stat-num  { font-family: var(--mono); font-size: 22px; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.12em; margin-top: 2px; }

/* ── Safety block ── */
.safety-block {
    background: #FFF7F7; border: 1px solid rgba(220,38,38,0.18);
    border-radius: 8px; padding: 12px 14px;
    font-family: var(--mono); font-size: 11px;
    color: var(--danger); line-height: 1.8;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important; overflow: hidden !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: rgba(124,58,237,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(124,58,237,0.38); }

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Session State ────────────────────────────────────────────────
if "df"       not in st.session_state: st.session_state.df       = None
if "history"  not in st.session_state: st.session_state.history  = []
if "filename" not in st.session_state: st.session_state.filename = None
if "examples" not in st.session_state: st.session_state.examples = []

# ── Helper: safely append result ────────────────────────────────
def safe_append(question: str, result):
    """Guarantees history always gets a proper dict, never crashes."""
    if isinstance(result, dict):
        entry = {"question": question, **result}
        # ensure all keys exist
        entry.setdefault("type",    "text")
        entry.setdefault("answer",  None)
        entry.setdefault("fig",     None)
        entry.setdefault("insight", None)
    else:
        entry = {
            "question": question,
            "type":     "text",
            "answer":   str(result),
            "fig":      None,
            "insight":  None,
        }
    st.session_state.history.append(entry)

# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        AI-Powered Data Analysis
        <span>◈ Querio</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;color:#9490B0;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:10px;">Data Source</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("", type=["csv"], label_visibility="collapsed")

    if uploaded_file:
        df_new = pd.read_csv(uploaded_file)
        # Regenerate examples only when a new file is uploaded
        if uploaded_file.name != st.session_state.filename:
            st.session_state.df       = df_new
            st.session_state.filename = uploaded_file.name
            st.session_state.history  = []
            with st.spinner("Generating smart examples..."):
                st.session_state.examples = generate_examples(df_new)
        else:
            st.session_state.df = df_new

        rows = len(st.session_state.df)
        cols = len(st.session_state.df.columns)
        st.markdown(f"""
        <div class="stat-row">
            <div class="stat-box"><div class="stat-num">{rows}</div><div class="stat-label">Rows</div></div>
            <div class="stat-box"><div class="stat-num">{cols}</div><div class="stat-label">Cols</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<p style="font-size:11px;color:#9490B0;text-transform:uppercase;letter-spacing:0.15em;margin:16px 0 8px;">Schema</p>', unsafe_allow_html=True)

        cols_html = ""
        for col, dtype in zip(st.session_state.df.columns, st.session_state.df.dtypes):
            dtype_short = str(dtype).replace("object","str").replace("int64","int").replace("float64","float")
            cols_html += f'<span class="col-pill">{col}<span class="dtype">{dtype_short}</span></span>'
        st.markdown(cols_html, unsafe_allow_html=True)

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:1px;background:rgba(124,58,237,0.10);margin:0 -1rem 16px"></div>', unsafe_allow_html=True)

    with st.expander("⚠ Blocked Operations"):
        from safety import safety_report
        st.markdown(f'<div class="safety-block">{safety_report().replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;color:#9490B0;text-align:center;margin-top:24px;font-family:\'Space Mono\',monospace;">Querio · Groq & LangGraph</p>', unsafe_allow_html=True)


# ── Main Content ─────────────────────────────────────────────────
col_main, col_pad = st.columns([3, 1])

with col_main:

    st.markdown("""
    <div style="padding:2rem 0 1.5rem">
        <div class="hero-title">Ask Your Data Anything</div>
        <div class="hero-heading">Meet <em>Querio.</em></div>
        <div style="font-size:24px;font-weight:500;color:#4C4769;letter-spacing:-0.01em;margin-top:-6px;margin-bottom:10px;">Query smarter.</div>
        <div class="hero-sub">Querio turns plain English into instant data answers — no SQL, no code, no waiting.</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="h-divider"></div>', unsafe_allow_html=True)

    # ── Query Section ─────────────────────────────────────────────
    if st.session_state.df is not None:

        fname = st.session_state.filename or "dataset.csv"
        st.markdown(f'<p style="font-family:\'Space Mono\',monospace;font-size:11px;color:#7C3AED;margin-bottom:16px;">▸ {fname} loaded and ready</p>', unsafe_allow_html=True)

        with st.expander("Preview data"):
            st.dataframe(st.session_state.df.head(8), use_container_width=True)

        st.markdown('<div class="h-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="query-label">Ask a question</div>', unsafe_allow_html=True)

        question = st.text_input(
            "", placeholder="e.g.  What is the average salary by department?",
            label_visibility="collapsed", key="query_input"
        )
        run_btn = st.button("▶  Run Query", type="primary")

        # Example chips
        st.markdown('<div style="margin-top:12px;margin-bottom:4px"><span style="font-size:11px;color:#9490B0;text-transform:uppercase;letter-spacing:0.1em;">Try an example</span></div>', unsafe_allow_html=True)

        examples = st.session_state.examples or [
            "Top 3 highest values?",
            "Average by category?",
            "Show data distribution",
            "Compare by group bar chart",
        ]
        chip_cols = st.columns(len(examples))
        for i, ex in enumerate(examples):
            with chip_cols[i]:
                if st.button(ex, key=f"chip_{i}"):
                    with st.spinner("◈ Thinking..."):
                        try:
                            result = run_agent(st.session_state.df, ex)
                            safe_append(ex, result)
                        except Exception as e:
                            safe_append(ex, f"⚠ Unexpected error: {e}")

        # ── Run agent ─────────────────────────────────────────────
        if run_btn and question:
            with st.spinner("◈ Querio is analyzing your data..."):
                try:
                    result = run_agent(st.session_state.df, question)
                    safe_append(question, result)
                except Exception as e:
                    safe_append(question, f"⚠ Unexpected error: {e}")

        # ── Results ───────────────────────────────────────────────
        if st.session_state.history:
            st.markdown('<div class="h-divider"></div>', unsafe_allow_html=True)
            latest = st.session_state.history[-1]

            # EDA result
            if latest.get("type") == "eda":
                st.markdown(f"""
                <div class="answer-card">
                    <div class="answer-label">Visualization</div>
                    <div class="answer-question">Q: {latest['question']}</div>
                </div>""", unsafe_allow_html=True)

                if latest.get("fig"):
                    st.plotly_chart(latest["fig"], use_container_width=True, config={"displayModeBar": False})
                else:
                    st.warning("Could not generate a chart for this question. Try rephrasing.")

                if latest.get("insight"):
                    st.markdown(f"""
                    <div class="insight-card">
                        <div class="insight-label">◈ Data Insight</div>
                        <div class="insight-text">{latest['insight']}</div>
                    </div>""", unsafe_allow_html=True)

            # Text result
            else:
                answer_text = latest.get("answer") or ""
                is_error    = str(answer_text).startswith("⚠")
                card_class  = "error-card" if is_error else "answer-card"

                if is_error:
                    st.markdown(f'<div class="{card_class}">{answer_text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="answer-card">
                        <div class="answer-label">Result</div>
                        <div class="answer-question">Q: {latest['question']}</div>
                        <div class="answer-text">{answer_text.replace(chr(10),'<br>')}</div>
                    </div>""", unsafe_allow_html=True)

            # History
            if len(st.session_state.history) > 1:
                st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
                with st.expander(f"History  ({len(st.session_state.history)-1} previous)"):
                    for item in reversed(st.session_state.history[:-1]):
                        result_type = item.get("type", "text")
                        preview     = item.get("insight") or item.get("answer") or ""
                        tag         = "📊 Chart" if result_type == "eda" else "💬 Answer"
                        st.markdown(f"""
                        <div class="history-item">
                            <div class="history-q">{tag} &nbsp;·&nbsp; Q: {item['question']}</div>
                            <div class="history-a">{str(preview)[:180]}{'...' if len(str(preview))>180 else ''}</div>
                        </div>""", unsafe_allow_html=True)

    else:
        # Empty state
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">◈</div>
            <div class="empty-title">No data loaded yet</div>
            <div class="empty-sub">Upload a CSV from the sidebar<br>to start asking questions</div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="h-divider"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:11px;color:#9490B0;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:16px;">Example questions you can ask</p>', unsafe_allow_html=True)

        examples_display = [
            ("What is the average salary by department?",           "Aggregation"),
            ("Who are the top 3 highest paid employees?",           "Ranking"),
            ("Show salary distribution across all employees",       "Chart"),
            ("Compare salary vs years of experience scatter plot",  "Chart"),
            ("Show salary breakdown by department bar chart",       "Chart"),
            ("What is the correlation between experience and salary?", "Analysis"),
        ]
        for q, tag in examples_display:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid rgba(124,58,237,0.07)">
                <span style="font-size:10px;font-family:'Space Mono',monospace;color:#7C3AED;background:rgba(124,58,237,0.09);border-radius:4px;padding:2px 8px;white-space:nowrap">{tag}</span>
                <span style="font-size:14px;color:#4C4769">{q}</span>
            </div>""", unsafe_allow_html=True)