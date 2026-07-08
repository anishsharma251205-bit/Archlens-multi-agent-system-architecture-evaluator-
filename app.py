import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import plotly.graph_objects as go
from agents.orchestrator import evaluate
from core.scoring import get_score_label
from core.llm_client import describe_diagram
from fpdf import FPDF
from datetime import datetime
import re

st.set_page_config(page_title="ArchLens", page_icon="🔬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0D1117; }
.main .block-container { padding: 2rem 3rem; max-width: 1200px; }

.app-header { text-align: center; padding: 2.5rem 0 2rem; border-bottom: 1px solid #21262D; margin-bottom: 2rem; }
.app-title { font-size: 2.8rem; font-weight: 300; color: #E6EDF3; letter-spacing: -0.02em; margin: 0; }
.app-title b { font-weight: 600; color: #58A6FF; }
.app-caption { color: #8B949E; font-size: 14px; margin-top: 0.5rem; }

.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid #21262D; }
.stTabs [data-baseweb="tab"] { color: #8B949E; font-size: 13px; font-weight: 500; background: transparent; }
.stTabs [aria-selected="true"] { color: #58A6FF !important; border-bottom: 2px solid #58A6FF !important; background: transparent !important; }

.stTextArea textarea {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 8px !important;
    color: #E6EDF3 !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea textarea:focus { border-color: #58A6FF !important; }

.stButton > button {
    background: #238636 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 0.5rem 1.25rem !important;
}
.stButton > button:hover { background: #2EA043 !important; }
.stButton > button:disabled { background: #21262D !important; color: #484F58 !important; }

.score-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 1.5rem;
    text-align: center;
    margin-bottom: 1rem;
}
.score-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 3rem;
    font-weight: 400;
    color: #E6EDF3;
    line-height: 1;
}
.score-denom { font-size: 1.2rem; color: #8B949E; }
.score-label { font-size: 12px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.5rem; }
.label-excellent { color: #3FB950; }
.label-good { color: #58A6FF; }
.label-needs { color: #D29922; }
.label-critical { color: #F85149; }

.dim-row {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
}
.dim-row-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.dim-row-name { font-size: 12px; font-weight: 500; color: #C9D1D9; }
.dim-row-score { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 500; }
.dim-track { background: #21262D; border-radius: 3px; height: 4px; }
.dim-fill { height: 4px; border-radius: 3px; }

.issue-block {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
}
.sev-badge {
    font-size: 10px; font-weight: 600; letter-spacing: 0.08em;
    padding: 2px 8px; border-radius: 12px; display: inline-block; margin-bottom: 4px;
}
.sev-critical { background: #2D1515; color: #F85149; }
.sev-high { background: #2D1C10; color: #E8732A; }
.sev-medium { background: #2D2410; color: #D29922; }
.sev-low { background: #0D2119; color: #3FB950; }
.issue-title { font-size: 13px; font-weight: 500; color: #C9D1D9; margin-bottom: 3px; }
.issue-desc { font-size: 12px; color: #8B949E; line-height: 1.6; }

.report-wrap {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 10px;
    padding: 1.5rem 2rem;
    color: #8B949E;
    font-size: 13px;
    line-height: 1.8;
}
.report-wrap h1,.report-wrap h2,.report-wrap h3 { color: #C9D1D9; font-weight: 500; font-size: 14px; margin: 1.25rem 0 0.5rem; }
.report-wrap strong { color: #C9D1D9; }
.report-wrap ul, .report-wrap ol { padding-left: 1.25rem; }

.section-label {
    font-size: 11px; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: #484F58;
    border-bottom: 1px solid #21262D;
    padding-bottom: 6px; margin: 1.75rem 0 1rem;
}

.stDownloadButton > button {
    background: #161B22 !important;
    color: #58A6FF !important;
    border: 1px solid #30363D !important;
    border-radius: 6px !important;
    font-size: 13px !important;
}
.stDownloadButton > button:hover { border-color: #58A6FF !important; background: #1C2330 !important; }

hr { border-color: #21262D !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    replacements = {
        '\u2013': '-', '\u2014': '-', '\u2019': "'", '\u2018': "'",
        '\u201C': '"', '\u201D': '"', '\u2022': '-', '\u2026': '...',
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    text = re.sub(r'[#*`]', '', text)
    text = ''.join(c if ord(c) < 128 else '?' for c in text)
    return text


def safe_multi_cell(pdf, text):
    words = []
    for word in text.split():
        while len(word) > 35:
            words.append(word[:35])
            word = word[35:]
        words.append(word)
    line = ' '.join(words)
    try:
        pdf.multi_cell(0, 4, line)
    except Exception:
        pass


def bar_color(score):
    if score >= 7.5: return "#3FB950"
    if score >= 5.0: return "#58A6FF"
    if score >= 3.0: return "#D29922"
    return "#F85149"


def label_class(label):
    return {"Excellent": "label-excellent", "Good": "label-good",
            "Needs improvement": "label-needs",
            "Critical issues found": "label-critical"}.get(label, "label-good")


def sev_class(sev):
    return {"critical": "sev-critical", "high": "sev-high",
            "medium": "sev-medium", "low": "sev-low"}.get(sev, "sev-low")


def generate_pdf(result) -> bytes:
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(20, 30, 50)
    pdf.cell(0, 10, "ArchLens Evaluation Report", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 110, 130)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", ln=True)
    pdf.ln(5)

    # Overall score
    pdf.set_fill_color(235, 242, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(20, 60, 120)
    label = get_score_label(result.final_score)
    pdf.cell(0, 9, f"  Overall Score: {result.final_score}/10  --  {label}",
             ln=True, fill=True)
    pdf.ln(4)

    # Dimension scores
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 30, 50)
    pdf.cell(0, 7, "Dimension Scores", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 70, 90)
    for name, score in [
        ("Structure",   result.structure.score),
        ("Security",    result.security.score),
        ("Scalability", result.scalability.score),
        ("Performance", result.performance.score),
        ("Cost",        result.cost.score),
    ]:
        pdf.cell(55, 6, f"  {name}", border=0)
        pdf.cell(0, 6, f"{score} / 10", ln=True)
    pdf.ln(4)

    # Full report
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 30, 50)
    pdf.cell(0, 7, "Evaluation Report", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(70, 80, 100)
    for line in clean_text(result.final_report).split('\n'):
        line = line.strip()
        if not line:
            pdf.ln(2)
        else:
            safe_multi_cell(pdf, line)
    pdf.ln(4)

    # Issues
    for dim in [result.structure, result.security, result.scalability,
                result.performance, result.cost]:
        if not dim.issues:
            continue
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(20, 30, 50)
        pdf.cell(0, 6, f"{dim.dimension.title()} -- Issues", ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(70, 80, 100)
        for issue in dim.issues:
            safe_multi_cell(pdf,
                f"[{issue.severity.value.upper()}] {issue.title}: "
                f"{clean_text(issue.description)}")
        pdf.ln(2)

    return bytes(pdf.output())


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-title">Arch<b>Lens</b></div>
    <div class="app-caption">Multi-agent AI · System architecture evaluator</div>
</div>
""", unsafe_allow_html=True)

# ── Input tabs ────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📝  Text description", "🖼️  Upload diagram"])
system_description = None

with tab1:
    text_input = st.text_area(
        "Describe your system architecture",
        height=180,
        placeholder="Example: A ride-sharing app with a React frontend, Node.js API gateway, "
                    "separate microservices for users, rides, and payments, PostgreSQL databases "
                    "per service, Redis for caching, and AWS deployment with ECS..."
    )
    if st.button("Evaluate architecture",
                 disabled=not bool(text_input and text_input.strip())):
        system_description = text_input

with tab2:
    uploaded_file = st.file_uploader(
        "Upload an architecture diagram", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded diagram", width=420)
        if st.button("Evaluate diagram"):
            with st.spinner("Reading diagram..."):
                image_bytes = uploaded_file.read()
                mime = uploaded_file.type
                description = describe_diagram(image_bytes, mime)
            with st.expander("Extracted description", expanded=False):
                st.write(description)
            system_description = description

# ── Run evaluation ────────────────────────────────────────────────────────────
if system_description:
    with st.spinner("Running evaluation agents..."):
        progress = st.progress(0, text="Analyzing structure...")
        result = evaluate(system_description)
        progress.progress(100, text="Complete.")
        progress.empty()

    label = get_score_label(result.final_score)

    st.markdown('<div class="section-label">Evaluation results</div>',
                unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1.8])

    with col1:
        lclass = label_class(label)
        st.markdown(f"""
        <div class="score-card">
            <div class="score-num">{result.final_score}
                <span class="score-denom">/10</span>
            </div>
            <div class="score-label {lclass}">{label}</div>
        </div>
        """, unsafe_allow_html=True)

        for name, score in [
            ("Structure",   result.structure.score),
            ("Security",    result.security.score),
            ("Scalability", result.scalability.score),
            ("Performance", result.performance.score),
            ("Cost",        result.cost.score),
        ]:
            color = bar_color(score)
            st.markdown(f"""
            <div class="dim-row">
                <div class="dim-row-header">
                    <span class="dim-row-name">{name}</span>
                    <span class="dim-row-score" style="color:{color}">{score}/10</span>
                </div>
                <div class="dim-track">
                    <div class="dim-fill" style="width:{score*10}%;background:{color}">
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        vals = [result.structure.score, result.security.score,
                result.scalability.score, result.performance.score,
                result.cost.score]
        cats = ["Structure", "Security", "Scalability", "Performance", "Cost"]
        fig = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself",
            fillcolor="rgba(88,166,255,0.1)",
            line=dict(color="#58A6FF", width=2),
            marker=dict(color="#58A6FF", size=5),
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="#161B22",
                radialaxis=dict(visible=True, range=[0, 10],
                                tickfont=dict(color="#484F58", size=9),
                                gridcolor="#21262D", linecolor="#21262D"),
                angularaxis=dict(tickfont=dict(color="#8B949E", size=12),
                                 gridcolor="#21262D", linecolor="#21262D"),
            ),
            paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
            showlegend=False, margin=dict(l=50, r=50, t=30, b=30), height=360,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Report
    st.markdown('<div class="section-label">Evaluation report</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="report-wrap">{result.final_report}</div>',
                unsafe_allow_html=True)

    # Dimension breakdown
    st.markdown('<div class="section-label">Dimension breakdown</div>',
                unsafe_allow_html=True)
    tabs = st.tabs(["Structure", "Security", "Scalability", "Performance", "Cost"])
    dims = [result.structure, result.security, result.scalability,
            result.performance, result.cost]

    for tab, dim in zip(tabs, dims):
        with tab:
            st.metric("Score", f"{dim.score} / 10")
            st.markdown(
                f'<p style="font-size:13px;color:#8B949E;line-height:1.8">'
                f'{dim.summary}</p>',
                unsafe_allow_html=True)

            if dim.issues:
                st.markdown('<div class="section-label">Issues</div>',
                            unsafe_allow_html=True)
                for issue in dim.issues:
                    sev = issue.severity.value
                    sc = sev_class(sev)
                    st.markdown(f"""
                    <div class="issue-block">
                        <span class="sev-badge {sc}">{sev.upper()}</span>
                        <div class="issue-title">{issue.title}</div>
                        <div class="issue-desc">{issue.description}</div>
                    </div>
                    """, unsafe_allow_html=True)

            if dim.recommendations:
                st.markdown('<div class="section-label">Recommendations</div>',
                            unsafe_allow_html=True)
                for i, rec in enumerate(dim.recommendations, 1):
                    st.markdown(
                        f'<p style="font-size:13px;color:#8B949E;line-height:1.8">'
                        f'<span style="color:#58A6FF;font-weight:600">{i}.</span>'
                        f' {rec}</p>',
                        unsafe_allow_html=True)

    # PDF export
    st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)
    pdf_data = generate_pdf(result)
    st.download_button(
        label="⬇  Download PDF report",
        data=pdf_data,
        file_name=f"archlens_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf",
    )