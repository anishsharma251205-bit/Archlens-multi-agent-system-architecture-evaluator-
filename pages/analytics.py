import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from core.mlops import get_metrics


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ArchLens Analytics",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# GLOBAL STYLE
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background:
            radial-gradient(
                circle at 10% 0%,
                rgba(70, 100, 180, 0.10),
                transparent 28%
            ),
            radial-gradient(
                circle at 90% 10%,
                rgba(130, 70, 180, 0.08),
                transparent 25%
            ),
            #030508;
    }

    .main .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* ---------- HEADER ---------- */

    .archlens-eyebrow {
        font-family: monospace;
        font-size: 11px;
        letter-spacing: 4px;
        color: rgba(255,255,255,0.35);
        margin-bottom: 8px;
    }

    .archlens-title {
        font-size: 42px;
        font-weight: 300;
        letter-spacing: -2px;
        margin-bottom: 4px;
    }

    .archlens-title span {
        font-weight: 700;
    }

    .archlens-subtitle {
        color: rgba(255,255,255,0.38);
        font-size: 14px;
        margin-bottom: 18px;
    }

    /* ---------- STATUS ---------- */

    .status {
        display: inline-block;
        padding: 6px 12px;
        border: 1px solid rgba(90, 230, 180, 0.25);
        background: rgba(90, 230, 180, 0.05);
        color: rgba(120,255,210,0.85);
        font-family: monospace;
        font-size: 10px;
        letter-spacing: 2px;
    }

    /* ---------- SECTION HEADERS ---------- */

    .section-title {
        margin-top: 30px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
        font-family: monospace;
        font-size: 10px;
        letter-spacing: 3px;
        color: rgba(255,255,255,0.30);
        text-transform: uppercase;
    }

    /* ---------- METRIC CARDS ---------- */

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.07);
        padding: 18px;
        min-height: 115px;
    }

    div[data-testid="stMetric"]:hover {
        border-color: rgba(150,180,255,0.25);
        background: rgba(255,255,255,0.035);
    }

    div[data-testid="stMetricLabel"] {
        font-family: monospace;
        font-size: 9px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: rgba(255,255,255,0.35);
    }

    div[data-testid="stMetricValue"] {
        font-family: monospace;
        font-size: 28px;
        font-weight: 700;
    }

    /* ---------- DATAFRAME ---------- */

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255,255,255,0.07);
    }

    /* ---------- BUTTON ---------- */

    .stButton button {
        border-radius: 2px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.10);
    }

    .stButton button:hover {
        border-color: rgba(150,180,255,0.35);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="archlens-eyebrow">ARCHLENS // AI OBSERVABILITY</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="archlens-title">Arch<span>Lens</span> Analytics</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="archlens-subtitle">'
    'Architecture intelligence · evaluation telemetry · system health'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="status">● SYSTEM OPERATIONAL</div>',
    unsafe_allow_html=True,
)


# ============================================================
# LOAD DATA
# ============================================================

metrics = get_metrics()

total_runs = metrics.get("total_evaluations", 0)

if total_runs == 0:

    st.info(
        "No evaluations recorded yet. "
        "Run your first architecture evaluation to populate analytics."
    )

    st.stop()


# ============================================================
# SYSTEM HEALTH
# ============================================================

st.markdown(
    '<div class="section-title">✦ System Health</div>',
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Total Runs",
        total_runs,
    )

with c2:
    st.metric(
        "Average Latency",
        f"{metrics.get('avg_latency_seconds', 0):.2f}s",
    )

with c3:
    st.metric(
        "JSON Failure Rate",
        f"{metrics.get('json_failure_rate', 0) * 100:.1f}%",
    )


# ============================================================
# AI QUALITY
# ============================================================

st.markdown(
    '<div class="section-title">✦ AI Quality</div>',
    unsafe_allow_html=True,
)

q1, q2, q3, q4 = st.columns(4)

with q1:
    st.metric(
        "Mean Score",
        f"{metrics.get('mean_score', 0):.2f}",
    )

with q2:
    st.metric(
        "Accuracy",
        f"{metrics.get('accuracy', 0) * 100:.1f}%",
    )

with q3:
    st.metric(
        "Score Deviation",
        f"{metrics.get('score_deviation', 0):.2f}",
    )

with q4:
    st.metric(
        "MAE",
        f"{metrics.get('mae', 0):.2f}",
    )


# ============================================================
# SCORE TREND
# ============================================================

st.markdown(
    '<div class="section-title">✦ Evaluation Performance</div>',
    unsafe_allow_html=True,
)

recent = metrics.get("recent_evaluations", [])

if recent:

    recent = list(reversed(recent))

    scores = [float(x["score"]) for x in recent]
    complexities = [x["complexity"] for x in recent]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(range(1, len(scores) + 1)),
            y=scores,
            mode="lines+markers",
            line=dict(
                color="rgba(150,180,255,0.9)",
                width=2,
            ),
            marker=dict(
                size=7,
                color="rgba(220,225,255,0.95)",
            ),
            customdata=complexities,
            hovertemplate=(
                "<b>Run %{x}</b><br>"
                "Score: %{y:.2f}<br>"
                "Complexity: %{customdata}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_hline(
        y=metrics.get("mean_score", 0),
        line_dash="dot",
        line_color="rgba(255,255,255,0.20)",
        annotation_text="MEAN",
        annotation_font=dict(
            size=9,
            color="rgba(255,255,255,0.35)",
        ),
    )

    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="monospace",
            color="rgba(255,255,255,0.45)",
        ),
        xaxis=dict(
            title="Evaluation Run",
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Score",
            range=[0, 10],
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# DISTRIBUTIONS
# ============================================================

st.markdown(
    '<div class="section-title">✦ Evaluation Distribution</div>',
    unsafe_allow_html=True,
)

left, right = st.columns(2)


# Complexity
with left:

    complexity = metrics.get("complexity_distribution", {})

    if complexity:

        fig = go.Figure(
            go.Bar(
                x=list(complexity.keys()),
                y=list(complexity.values()),
                marker=dict(
                    color="rgba(140,160,255,0.55)",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1,
                    ),
                ),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Runs: %{y}"
                    "<extra></extra>"
                ),
            )
        )

        fig.update_layout(
            title="Architecture Complexity",
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="monospace",
                color="rgba(255,255,255,0.45)",
            ),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.04)",
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.04)",
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# Model usage
with right:

    model_usage = metrics.get("model_usage", {})

    if model_usage:

        fig = go.Figure(
            go.Bar(
                x=list(model_usage.keys()),
                y=list(model_usage.values()),
                marker=dict(
                    color="rgba(180,130,255,0.55)",
                    line=dict(
                        color="rgba(255,255,255,0.15)",
                        width=1,
                    ),
                ),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Evaluations: %{y}"
                    "<extra></extra>"
                ),
            )
        )

        fig.update_layout(
            title="Model Usage",
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="monospace",
                color="rgba(255,255,255,0.45)",
            ),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.04)",
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.04)",
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ============================================================
# QUALITY GAUGE
# ============================================================

st.markdown(
    '<div class="section-title">✦ Evaluation Quality</div>',
    unsafe_allow_html=True,
)

accuracy = metrics.get("accuracy", 0) * 100

fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=accuracy,
        number=dict(
            suffix="%",
            font=dict(
                family="monospace",
                size=34,
            ),
        ),
        title=dict(
            text="Consistency / Accuracy",
            font=dict(
                family="monospace",
                size=11,
                color="rgba(255,255,255,0.40)",
            ),
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickfont=dict(
                    family="monospace",
                    size=9,
                    color="rgba(255,255,255,0.30)",
                ),
            ),
            bar=dict(
                color="rgba(150,180,255,0.75)",
            ),
            bgcolor="rgba(255,255,255,0.04)",
            bordercolor="rgba(255,255,255,0.08)",
            steps=[
                dict(
                    range=[0, 50],
                    color="rgba(255,255,255,0.015)",
                ),
                dict(
                    range=[50, 75],
                    color="rgba(255,255,255,0.025)",
                ),
                dict(
                    range=[75, 100],
                    color="rgba(255,255,255,0.045)",
                ),
            ],
        ),
    )
)

fig.update_layout(
    height=320,
    margin=dict(l=30, r=30, t=50, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)


# ============================================================
# SYSTEM INSIGHTS
# ============================================================

st.markdown(
    '<div class="section-title">✦ System Insights</div>',
    unsafe_allow_html=True,
)

i1, i2, i3 = st.columns(3)

hallucination_rate = metrics.get("hallucination_rate", 0)
json_failure_rate = metrics.get("json_failure_rate", 0)

with i1:

    if hallucination_rate == 0:
        st.success(
            "RELIABILITY\n\n"
            "No hallucination flags detected."
        )
    else:
        st.warning(
            f"RELIABILITY\n\n"
            f"{hallucination_rate * 100:.1f}% "
            "of evaluations triggered hallucination detection."
        )


with i2:

    if json_failure_rate == 0:
        st.success(
            "STRUCTURED OUTPUT\n\n"
            "All recorded evaluations returned valid JSON."
        )
    else:
        st.warning(
            f"STRUCTURED OUTPUT\n\n"
            f"{json_failure_rate * 100:.1f}% "
            "of evaluations encountered JSON failures."
        )


with i3:

    st.info(
        "EVALUATION STABILITY\n\n"
        f"Score deviation: "
        f"{metrics.get('score_deviation', 0):.2f}"
    )


# ============================================================
# RECENT RUNS
# ============================================================

st.markdown(
    '<div class="section-title">✦ Recent Evaluations</div>',
    unsafe_allow_html=True,
)

if recent:

    rows = []

    for index, run in enumerate(recent):

        score = float(run["score"])

        if score >= 8:
            status = "PASS"
        elif score >= 6:
            status = "WARN"
        else:
            status = "FAIL"

        rows.append(
            {
                "Run": f"RUN-{len(recent) - index:03d}",
                "Timestamp": run.get("timestamp", "")[:19],
                "Complexity": str(run["complexity"]).upper(),
                "Score": round(score, 2),
                "Status": status,
            }
        )

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.NumberColumn(
                "Score",
                format="%.2f",
            ),
        },
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        margin-top:50px;
        padding-top:20px;
        border-top:1px solid rgba(255,255,255,0.06);
        color:rgba(255,255,255,0.18);
        font-family:monospace;
        font-size:9px;
        letter-spacing:3px;
    ">
        ARCHLENS · AI ARCHITECTURE EVALUATION SYSTEM
    </div>
    """,
    unsafe_allow_html=True,
)