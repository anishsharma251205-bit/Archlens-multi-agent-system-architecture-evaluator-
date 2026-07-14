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
import random

st.set_page_config(page_title="ArchLens", page_icon="✦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&family=Space+Mono:wght@400;700&display=swap');

/* ── Reset ── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    color: #ffffff;
}
.stApp {
    background-color: #000000;
}
.main .block-container {
    padding: 2rem 3rem 4rem;
    max-width: 1200px;
    position: relative;
}

/* ── Shared cosmic background container ── */
.cosmic-bg {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}

/* ── Starfield (Overview page) ── */
.star {
    position: absolute;
    color: rgba(255,255,255,0.6);
    font-size: 10px;
    animation: twinkle var(--dur) ease-in-out infinite;
    animation-delay: var(--delay);
}
@keyframes twinkle {
    0%, 100% { opacity: 0.1; transform: scale(0.8); }
    50%       { opacity: 0.9; transform: scale(1.2); }
}

/* ── Comets (Export page) ── */
.comet {
    position: absolute;
    width: 2px; height: 2px;
    background: #ffffff;
    border-radius: 50%;
    box-shadow: 0 0 6px 2px rgba(255,255,255,0.5);
    animation: shoot 4s linear infinite;
    opacity: 0;
}
.comet::before {
    content: '';
    position: absolute;
    top: 1px; left: 1px;
    width: 90px; height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.55), transparent);
    transform: rotate(200deg);
    transform-origin: left center;
}
@keyframes shoot {
    0%   { opacity: 0; transform: translate(0, 0); }
    8%   { opacity: 1; }
    35%  { opacity: 0; transform: translate(-320px, 230px); }
    100% { opacity: 0; transform: translate(-320px, 230px); }
}

/* ── Real astrophoto orbs (screen-blended so black space melts into bg) ── */
.cs-photo-circle {
    position: absolute;
    border-radius: 50%;
    background-size: cover;
    background-position: center;
    mix-blend-mode: screen;
    filter: brightness(0.95) contrast(1.05);
    animation: orbfloat var(--dur) ease-in-out infinite;
}
.cs-photo-rect {
    position: absolute;
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    mix-blend-mode: screen;
    filter: brightness(0.95) contrast(1.05);
    animation: orbfloat var(--dur) ease-in-out infinite;
}
@keyframes orbfloat {
    0%, 100% { transform: translateY(0px); }
    50%       { transform: translateY(-18px); }
}
@keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}

/* ── Soft glow underlays (sit behind the real photos for extra depth) ── */
.cs-glow-warm {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,180,90,0.18) 0%, rgba(255,180,90,0) 70%);
    filter: blur(20px);
    animation: nebulapulse var(--dur) ease-in-out infinite;
}

/* ── Nebula clouds (Breakdown page) ── */
.nebula-cloud {
    position: absolute;
    border-radius: 50%;
    filter: blur(40px);
    animation: nebulapulse var(--dur) ease-in-out infinite;
}
@keyframes nebulapulse {
    0%, 100% { opacity: 0.15; transform: scale(1); }
    50%       { opacity: 0.3;  transform: scale(1.15); }
}

/* ── Tiny photo-credit caption ── */
.cs-credit {
    position: fixed;
    bottom: 8px; right: 12px;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.05em;
    color: rgba(255,255,255,0.15);
    z-index: 1;
}

/* ── Header ── */
.space-header {
    text-align: center;
    padding: 3.5rem 0 2.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 2.5rem;
    position: relative;
}
.header-eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.3em;
    color: rgba(255,255,255,0.35);
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}
.header-title {
    font-size: 4rem;
    font-weight: 300;
    color: #ffffff;
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1;
}
.header-title b {
    font-weight: 600;
}
.header-sub {
    font-size: 14px;
    color: rgba(255,255,255,0.3);
    margin-top: 1rem;
    font-weight: 300;
    letter-spacing: 0.05em;
}
.header-stars {
    font-size: 18px;
    color: rgba(255,255,255,0.4);
    margin-bottom: 1rem;
    letter-spacing: 1rem;
    animation: twinkle 3s ease-in-out infinite;
}

/* ── Page nav pills ── */
.nav-track {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.25);
    text-align: center;
    margin-bottom: 0.5rem;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(255,255,255,0.3) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #ffffff !important;
    border-bottom: 1px solid #ffffff !important;
    background: transparent !important;
}

/* ── Text area ── */
.stTextArea textarea {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 0 !important;
    color: #ffffff !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 13px !important;
    line-height: 1.8 !important;
}
.stTextArea textarea:focus {
    border-color: rgba(255,255,255,0.4) !important;
    box-shadow: none !important;
}
.stTextArea textarea::placeholder {
    color: rgba(255,255,255,0.2) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: transparent !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.4) !important;
    border-radius: 0 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    background: rgba(255,255,255,0.06) !important;
    border-color: #ffffff !important;
}
.stButton > button:disabled {
    color: rgba(255,255,255,0.85) !important;
    border-color: rgba(255,255,255,0.7) !important;
    background: rgba(255,255,255,0.08) !important;
}

/* ── File uploader ── */
div[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(255,255,255,0.12) !important;
    border-radius: 0 !important;
}

/* ── Score card ── */
.score-card {
    border: 1px solid rgba(255,255,255,0.12);
    padding: 2rem;
    text-align: center;
    margin-bottom: 1rem;
    position: relative;
    background: rgba(255,255,255,0.02);
}
.score-card::before {
    content: '✦';
    position: absolute;
    top: 12px; left: 12px;
    font-size: 10px;
    color: rgba(255,255,255,0.3);
}
.score-card::after {
    content: '✦';
    position: absolute;
    bottom: 12px; right: 12px;
    font-size: 10px;
    color: rgba(255,255,255,0.3);
}
.score-num {
    font-family: 'Space Mono', monospace;
    font-size: 4rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
    letter-spacing: -0.02em;
}
.score-denom {
    font-size: 1.5rem;
    color: rgba(255,255,255,0.25);
    font-weight: 400;
}
.score-verdict {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    margin-top: 0.75rem;
    color: rgba(255,255,255,0.5);
}
.score-excellent { color: rgba(255,255,255,0.9) !important; }
.score-good      { color: rgba(255,255,255,0.7) !important; }
.score-needs     { color: rgba(255,255,255,0.5) !important; }
.score-critical  { color: rgba(255,255,255,0.3) !important; }

/* ── Dimension rows ── */
.dim-row {
    border: 1px solid rgba(255,255,255,0.06);
    padding: 10px 14px;
    margin-bottom: 4px;
    background: rgba(255,255,255,0.01);
}
.dim-row-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 7px;
}
.dim-name {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45);
}
.dim-score {
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    color: #ffffff;
}
.dim-track {
    background: rgba(255,255,255,0.06);
    height: 1px;
}
.dim-fill {
    height: 1px;
    background: rgba(255,255,255,0.6);
}

/* ── Section label ── */
.section-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.2);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding-bottom: 8px;
    margin: 2rem 0 1rem;
}

/* ── Report block ── */
.report-block {
    border: 1px solid rgba(255,255,255,0.06);
    padding: 1.5rem 2rem;
    background: rgba(255,255,255,0.01);
    font-size: 13px;
    line-height: 1.9;
    color: rgba(255,255,255,0.6);
}
.report-block h1,
.report-block h2,
.report-block h3 {
    color: rgba(255,255,255,0.85);
    font-weight: 600;
    letter-spacing: 0.05em;
    margin: 1.25rem 0 0.5rem;
    font-family: 'Space Mono', monospace;
    text-transform: uppercase;
    font-size: 11px;
}
.report-block strong { color: rgba(255,255,255,0.8); }
.report-block ul, .report-block ol { padding-left: 1.25rem; }
.report-block li { margin-bottom: 4px; }

/* ── Issue cards ── */
.issue-card {
    border-left: 1px solid rgba(255,255,255,0.15);
    padding: 10px 14px;
    margin-bottom: 6px;
    background: rgba(255,255,255,0.01);
}
.issue-sev {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.sev-critical { color: rgba(255,255,255,0.9); }
.sev-high     { color: rgba(255,255,255,0.7); }
.sev-medium   { color: rgba(255,255,255,0.5); }
.sev-low      { color: rgba(255,255,255,0.3); }
.issue-title {
    font-size: 13px;
    font-weight: 500;
    color: rgba(255,255,255,0.85);
    margin-bottom: 3px;
}
.issue-desc {
    font-size: 12px;
    color: rgba(255,255,255,0.35);
    line-height: 1.6;
}

/* ── Metric override ── */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    padding: 1rem !important;
}
div[data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    color: #ffffff !important;
}
div[data-testid="stMetricLabel"] {
    color: rgba(255,255,255,0.3) !important;
    font-size: 10px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: transparent !important;
    color: rgba(255,255,255,0.5) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 0 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
}
.stDownloadButton > button:hover {
    color: #ffffff !important;
    border-color: rgba(255,255,255,0.4) !important;
    background: rgba(255,255,255,0.03) !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: rgba(255,255,255,0.4) !important; }

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── Expander ── */
details {
    border: 1px solid rgba(255,255,255,0.06) !important;
    background: rgba(255,255,255,0.01) !important;
}
summary {
    color: rgba(255,255,255,0.4) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.1em !important;
}

/* ── Progress bar ── */
.stProgress > div > div {
    background: rgba(255,255,255,0.12) !important;
}
.stProgress > div > div > div {
    background: rgba(255,255,255,0.7) !important;
}

/* ── Info box ── */
div[data-testid="stInfo"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.5) !important;
    border-radius: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Page registry ────────────────────────────────────────────────────────
PAGE_NAMES = ["Overview", "Report", "Breakdown", "Export"]
PAGE_ICONS = ["✦", "🪐", "🌌", "🌠"]

# ── Real NASA / APOD astrophotography used as page backdrops ─────────────
# (all public-domain / NASA imagery or CC-licensed with credit given below)
JUPITER_URL   = "https://d2pn8kiwq2w21t.cloudfront.net/original_images/jpegPIA01509.jpg"   # NASA/JPL, Voyager 1
SATURN_URL    = "https://apod.nasa.gov/apod/image/2406/SaturnColors_CassiniSchmidt_960.jpg" # NASA/ESA/JPL/SSI, proc. J. Schmidt (CC BY 2.0)

PAGE_CREDITS = [
    "Jupiter — NASA / JPL (Voyager 1)",
    "Saturn — NASA / ESA / JPL / SSI, proc. J. Schmidt",
]

# ── Background renderers (one distinct astronomical theme per page) ──────
def render_starfield():
    """Overview page: twinkling starfield + a real close-up of Jupiter."""
    positions = [
        (5,8),(12,22),(18,65),(25,40),(30,15),(35,78),(42,55),(48,30),
        (55,88),(60,12),(65,45),(70,70),(75,25),(80,60),(85,35),(90,80),
        (8,50),(20,90),(38,5),(52,75),(68,20),(82,92),(95,48),(3,38),
        (15,72),(28,18),(45,85),(58,42),(72,10),(88,65),(93,28),(10,95),
        (22,33),(40,60),(62,82),(78,50),(50,50),(33,95),(85,15),(48,68),
    ]
    html = '<div class="cosmic-bg">'
    for top, left in positions:
        dur = random.uniform(2, 6)
        delay = random.uniform(0, 4)
        html += f'<span class="star" style="top:{top}%;left:{left}%;--dur:{dur}s;--delay:{delay}s">✦</span>'
    html += (
        f'<div class="cs-photo-circle" style="top:-10%;right:-8%;width:480px;height:480px;'
        f'background-image:url(\'{JUPITER_URL}\');--dur:16s"></div>'
    )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_planets():
    """Report page: a large real photo of Saturn and its rings."""
    html = '<div class="cosmic-bg">'
    html += (
        f'<div class="cs-photo-rect" style="bottom:-10%;left:-8%;width:640px;height:420px;'
        f'background-image:url(\'{SATURN_URL}\');--dur:20s"></div>'
    )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_galaxy():
    """Breakdown page: the real Webb Pillars of Creation photo drifting amid nebula clouds."""
    clouds = [
        {"top": "8%",  "left": "68%", "size": 260, "color": "88,120,255",  "dur": 10},
        {"top": "62%", "left": "6%",  "size": 220, "color": "255,110,180", "dur": 13},
        {"top": "74%", "left": "70%", "size": 180, "color": "140,255,220", "dur": 9},
    ]
    html = '<div class="cosmic-bg">'
    for c in clouds:
        html += (
            f'<div class="nebula-cloud" style="top:{c["top"]};left:{c["left"]};'
            f'width:{c["size"]}px;height:{c["size"]}px;'
            f'background:rgba({c["color"]},0.25);--dur:{c["dur"]}s"></div>'
        )
    html += (
        f'<div class="cs-glow-warm" style="top:12%;left:26%;width:520px;height:520px;--dur:18s"></div>'
    )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_comets():
    """Export page: the real Andromeda Galaxy glowing softly with comets streaking past."""
    trails = [(5,12,0.0),(18,55,1.4),(32,80,2.6),(48,25,0.8),(62,68,3.2),(78,40,1.9),(88,85,2.3)]
    html = '<div class="cosmic-bg">'
    html += (
        f'<div class="cs-glow-warm" style="top:-14%;right:-10%;width:500px;height:500px;--dur:9s"></div>'
    )
    for top, left, delay in trails:
        html += f'<div class="comet" style="top:{top}%;left:{left}%;animation-delay:{delay}s"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

BACKGROUND_RENDERERS = [render_starfield, render_planets, render_galaxy, render_comets]

# ── Helpers ────────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    replacements = {
        '\u2013': '-', '\u2014': '-', '\u2019': "'", '\u2018': "'",
        '\u201C': '"', '\u201D': '"', '\u2022': '-', '\u2026': '...',
    }
    for ch, rep in replacements.items():
        text = text.replace(ch, rep)
    text = re.sub(r'[#*`]', '', text)
    return ''.join(c if ord(c) < 128 else '?' for c in text)

def safe_cell(pdf, text):
    words = []
    for w in text.split():
        while len(w) > 35:
            words.append(w[:35]); w = w[35:]
        words.append(w)
    try: pdf.multi_cell(0, 4, ' '.join(words))
    except: pass

def verdict_class(label):
    return {'Excellent': 'score-excellent', 'Good': 'score-good',
            'Needs improvement': 'score-needs',
            'Critical issues found': 'score-critical'}.get(label, 'score-good')

def sev_class(sev):
    return {'critical': 'sev-critical', 'high': 'sev-high',
            'medium': 'sev-medium', 'low': 'sev-low'}.get(sev, 'sev-low')

def generate_pdf(result) -> bytes:
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(10, 10, 10)
    pdf.cell(0, 10, "ArchLens Evaluation Report", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", ln=True)
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(10, 10, 10)
    label = get_score_label(result.final_score)
    pdf.cell(0, 9, f"  Overall Score: {result.final_score}/10  --  {label}", ln=True, fill=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Dimension Scores", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    for name, score in [("Structure", result.structure.score),
                         ("Security", result.security.score),
                         ("Scalability", result.scalability.score),
                         ("Performance", result.performance.score),
                         ("Cost", result.cost.score)]:
        pdf.cell(55, 6, f"  {name}", border=0)
        pdf.cell(0, 6, f"{score} / 10", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(10, 10, 10)
    pdf.cell(0, 7, "Evaluation Report", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(60, 60, 60)
    for line in clean_text(result.final_report).split('\n'):
        line = line.strip()
        if not line: pdf.ln(2)
        else: safe_cell(pdf, line)
    pdf.ln(3)
    for dim in [result.structure, result.security, result.scalability,
                result.performance, result.cost]:
        if not dim.issues: continue
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(10, 10, 10)
        pdf.cell(0, 6, f"{dim.dimension.title()} -- Issues", ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(60, 60, 60)
        for issue in dim.issues:
            safe_cell(pdf, f"[{issue.severity.value.upper()}] {issue.title}: {clean_text(issue.description)}")
        pdf.ln(2)
    return bytes(pdf.output())

# ── Session state ─────────────────────────────────────────────────────────
if "stage" not in st.session_state:
    st.session_state.stage = "input"      # "input" or "results"
if "page" not in st.session_state:
    st.session_state.page = 0             # index into PAGE_NAMES
if "result" not in st.session_state:
    st.session_state.result = None

def go_to_page(idx):
    st.session_state.page = idx
    st.rerun()

def reset_to_input():
    st.session_state.stage = "input"
    st.session_state.page = 0
    st.session_state.result = None
    st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="space-header">
    <div class="header-stars">✦ &nbsp; ✦ &nbsp; ✦</div>
    <div class="header-eyebrow">Multi-Agent AI · Architecture Analysis</div>
    <div class="header-title">Arch<b>Lens</b></div>
    <div class="header-sub">evaluate your system architecture across five engineering dimensions</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# STAGE 1 — INPUT
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.stage == "input":
    render_starfield()

    tab1, tab2 = st.tabs(["✦  Text description", "✦  Upload diagram"])
    system_description = None

    with tab1:
        text_input = st.text_area(
            label="arch",
            label_visibility="collapsed",
            height=160,
            placeholder="describe your system — components, databases, deployment, communication patterns, tech stack...",
            key="text_input"
        )
        if st.button("✦  Evaluate architecture",
                     disabled=not bool(text_input and text_input.strip())):
            system_description = text_input

    with tab2:
        uploaded_file = st.file_uploader(
            label="diagram",
            label_visibility="collapsed",
            type=["png", "jpg", "jpeg"],
            key="diagram"
        )
        if uploaded_file:
            st.image(uploaded_file, width=420)
            if st.button("✦  Evaluate diagram"):
                with st.spinner("reading diagram..."):
                    image_bytes = uploaded_file.read()
                    mime = uploaded_file.type
                    description = describe_diagram(image_bytes, mime)
                with st.expander("extracted description"):
                    st.write(description)
                system_description = description

    if system_description:
        with st.spinner("agents are thinking..."):
            progress = st.progress(0, text="initializing...")
            result = evaluate(system_description)
            progress.progress(100, text="complete.")
            progress.empty()
        st.session_state.result = result
        st.session_state.stage = "results"
        st.session_state.page = 0
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# STAGE 2 — RESULTS (multi-page, each with its own astronomical backdrop)
# ══════════════════════════════════════════════════════════════════════════
else:
    result = st.session_state.result
    label = get_score_label(result.final_score)
    vclass = verdict_class(label)
    page = st.session_state.page

    # themed background for the current page
    BACKGROUND_RENDERERS[page]()
    if page < len(PAGE_CREDITS):
        st.markdown(f'<div class="cs-credit">{PAGE_CREDITS[page]}</div>', unsafe_allow_html=True)

    # ── page nav pills ──
    st.markdown(f'<div class="nav-track">page {page + 1} / {len(PAGE_NAMES)}</div>',
                unsafe_allow_html=True)
    nav_cols = st.columns(len(PAGE_NAMES))
    for i, col in enumerate(nav_cols):
        with col:
            if st.button(f"{PAGE_ICONS[i]}  {PAGE_NAMES[i]}", key=f"nav_{i}",
                         disabled=(i == page), use_container_width=True):
                go_to_page(i)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PAGE 0 · OVERVIEW (starfield) ──
    if page == 0:
        st.markdown('<div class="section-label">✦ &nbsp; evaluation overview</div>',
                    unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1.8])

        with col1:
            st.markdown(f"""
            <div class="score-card">
                <div class="score-num">{result.final_score}
                    <span class="score-denom">/10</span>
                </div>
                <div class="score-verdict {vclass}">{label}</div>
            </div>
            """, unsafe_allow_html=True)

            for name, score in [
                ("Structure",   result.structure.score),
                ("Security",    result.security.score),
                ("Scalability", result.scalability.score),
                ("Performance", result.performance.score),
                ("Cost",        result.cost.score),
            ]:
                pct = score * 10
                st.markdown(f"""
                <div class="dim-row">
                    <div class="dim-row-header">
                        <span class="dim-name">{name}</span>
                        <span class="dim-score">{score}</span>
                    </div>
                    <div class="dim-track">
                        <div class="dim-fill" style="width:{pct}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            vals = [result.structure.score, result.security.score,
                    result.scalability.score, result.performance.score,
                    result.cost.score]
            cats = ["Structure", "Security", "Scalability", "Performance", "Cost"]
            fig = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=cats + [cats[0]],
                fill="toself",
                fillcolor="rgba(255,255,255,0.03)",
                line=dict(color="rgba(255,255,255,0.5)", width=1),
                marker=dict(color="rgba(255,255,255,0.8)", size=4),
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=True, range=[0, 10],
                        tickfont=dict(color="rgba(255,255,255,0.2)", size=9,
                                      family="Space Mono"),
                        gridcolor="rgba(255,255,255,0.06)",
                        linecolor="rgba(255,255,255,0.06)",
                    ),
                    angularaxis=dict(
                        tickfont=dict(color="rgba(255,255,255,0.4)", size=11,
                                      family="Space Mono"),
                        gridcolor="rgba(255,255,255,0.06)",
                        linecolor="rgba(255,255,255,0.06)",
                    ),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=50, r=50, t=30, b=30),
                height=370,
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── PAGE 1 · REPORT (planets) ──
    elif page == 1:
        st.markdown('<div class="section-label">🪐 &nbsp; evaluation report</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="report-block">{result.final_report}</div>',
                    unsafe_allow_html=True)

    # ── PAGE 2 · BREAKDOWN (galaxy) ──
    elif page == 2:
        st.markdown('<div class="section-label">🌌 &nbsp; dimension breakdown</div>',
                    unsafe_allow_html=True)
        tabs = st.tabs(["Structure", "Security", "Scalability", "Performance", "Cost"])
        dims = [result.structure, result.security, result.scalability,
                result.performance, result.cost]

        for tab, dim in zip(tabs, dims):
            with tab:
                st.metric("Score", f"{dim.score} / 10")
                st.markdown(
                    f'<p style="font-size:13px;color:rgba(255,255,255,0.4);'
                    f'line-height:1.8;margin-top:0.75rem">{dim.summary}</p>',
                    unsafe_allow_html=True)

                if dim.issues:
                    st.markdown('<div class="section-label">issues</div>',
                                unsafe_allow_html=True)
                    for issue in dim.issues:
                        sev = issue.severity.value
                        sc = sev_class(sev)
                        st.markdown(f"""
                        <div class="issue-card">
                            <div class="issue-sev {sc}">✦ &nbsp; {sev}</div>
                            <div class="issue-title">{issue.title}</div>
                            <div class="issue-desc">{issue.description}</div>
                        </div>
                        """, unsafe_allow_html=True)

                if dim.recommendations:
                    st.markdown('<div class="section-label">recommendations</div>',
                                unsafe_allow_html=True)
                    for i, rec in enumerate(dim.recommendations, 1):
                        st.markdown(
                            f'<p style="font-size:13px;color:rgba(255,255,255,0.4);'
                            f'line-height:1.8;margin:0 0 6px 0">'
                            f'<span style="font-family:Space Mono,monospace;'
                            f'color:rgba(255,255,255,0.2);font-size:11px">'
                            f'0{i} &nbsp;</span>{rec}</p>',
                            unsafe_allow_html=True)

    # ── PAGE 3 · EXPORT (comets) ──
    elif page == 3:
        st.markdown('<div class="section-label">🌠 &nbsp; export</div>',
                    unsafe_allow_html=True)
        pdf_data = generate_pdf(result)
        st.download_button(
            label="✦  Download PDF report",
            data=pdf_data,
            file_name=f"archlens_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
        )

    # ── bottom navigation ──
    st.markdown("<br>", unsafe_allow_html=True)
    prev_col, mid_col, next_col = st.columns([1, 2, 1])
    with prev_col:
        if page > 0:
            if st.button("←  Previous", key="prev_btn"):
                go_to_page(page - 1)
    with mid_col:
        if st.button("↺  New evaluation", key="reset_btn", use_container_width=True):
            reset_to_input()
    with next_col:
        if page < len(PAGE_NAMES) - 1:
            if st.button("Next  →", key="next_btn"):
                go_to_page(page + 1)