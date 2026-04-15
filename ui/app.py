import streamlit as st
import pandas as pd
import sqlite3
import time
import altair as alt
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
#  DIRECTORY CONFIG  (unchanged)
# ─────────────────────────────────────────────
ROOT_DIR    = Path(__file__).parent.parent.resolve()
DB_PATH     = ROOT_DIR / "automation.db"
SCAN_FLAG   = ROOT_DIR / "scan.flag"
RESCUE_FLAG = ROOT_DIR / "rescue.flag"

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="FileFlow — Automation Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  SESSION STATE  (new – drives feedback UI)
# ─────────────────────────────────────────────
# op_status  : "idle" | "scanning" | "rescuing" | "scan_done" | "rescue_done"
# op_step    : int  (0-based index of current progress step)
# op_ts      : timestamp of last operation start
for key, default in [
    ("op_status", "idle"),
    ("op_step",   0),
    ("op_ts",     None),
    ("last_count", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Step definitions for each operation
SCAN_STEPS = [
    ("🔎", "Initialising scanner…",        "Preparing file system access"),
    ("📂", "Reading root directory…",      "Listing all top-level entries"),
    ("🧬", "Detecting file types…",        "Matching extensions & MIME types"),
    ("🗂️", "Classifying content…",         "Applying category rules"),
    ("🚀", "Moving files to buckets…",     "Writing to destination folders"),
]

RESCUE_STEPS = [
    ("🚜", "Launching deep rescue…",       "Initialising recursive traversal"),
    ("🌲", "Traversing sub-folders…",      "Scanning all nested directories"),
    ("🔍", "Identifying misplaced files…", "Cross-checking placement rules"),
    ("⚙️", "Applying organisation rules…", "Reassigning files to correct buckets"),
    ("✨", "Cleaning up structure…",        "Removing empty folders & writing log"),
]


# ─────────────────────────────────────────────
#  GLOBAL STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;500;600;700&family=Figtree:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── CSS Variables ─────────────────────────── */
:root {
    --bg-base:       #06090f;
    --bg-surface:    #0c1220;
    --bg-card:       #0e1726;
    --border:        #162235;
    --border-bright: #1e3550;
    --text-primary:  #e8f1fc;
    --text-muted:    #4a6880;
    --text-faint:    #243040;
    --accent-blue:   #38bdf8;
    --accent-indigo: #818cf8;
    --accent-cyan:   #22d3ee;
    --accent-green:  #34d399;
    --accent-amber:  #fbbf24;
    --accent-pink:   #f472b6;
    --font-display:  'Bebas Neue', sans-serif;
    --font-sub:      'Rajdhani', sans-serif;
    --font-body:     'Figtree', sans-serif;
    --font-mono:     'JetBrains Mono', monospace;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: var(--font-body);
    font-size: 14px;
    color: var(--text-primary);
}

.stApp {
    background-color: var(--bg-base);
    background-image:
        radial-gradient(ellipse 100% 55% at 50% -5%,  rgba(56,189,248,.07)  0%, transparent 70%),
        radial-gradient(ellipse  50% 35% at 95% 90%,  rgba(129,140,248,.05) 0%, transparent 70%),
        radial-gradient(ellipse  30% 25% at  5% 70%,  rgba(34,211,238,.04)  0%, transparent 70%);
}

.block-container { padding: 0 2.5rem 5rem !important; max-width: 1440px !important; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1a2d42; border-radius: 99px; }


/* ══════════════════════════════════════════════
   OPERATION CARDS  (replaces old small buttons)
══════════════════════════════════════════════ */
.op-card {
    position: relative;
    border-radius: 14px;
    padding: 1.1rem 1.2rem 1rem;
    margin-bottom: 0.9rem;
    overflow: hidden;
    border: 1px solid var(--border);
    background: var(--bg-card);
    transition: border-color .2s, transform .15s;
}

.op-card:hover { border-color: var(--border-bright); transform: translateY(-1px); }

/* top accent bar */
.op-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--card-accent, linear-gradient(90deg,#38bdf8,#818cf8));
    border-radius: 14px 14px 0 0;
}

.op-card-scan   { --card-accent: linear-gradient(90deg,#38bdf8,#22d3ee); }
.op-card-rescue { --card-accent: linear-gradient(90deg,#fbbf24,#f472b6); }

.op-card-icon {
    font-size: 1.5rem;
    margin-bottom: 0.35rem;
    display: block;
    line-height: 1;
}

.op-card-title {
    font-family: var(--font-sub);
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--text-primary);
    margin-bottom: 0.15rem;
}

.op-card-desc {
    font-family: var(--font-body);
    font-size: 0.73rem;
    color: var(--text-muted);
    line-height: 1.4;
    margin-bottom: 0.75rem;
}

/* ── Primary action button (SCAN) ────────── */
.btn-scan {
    display: block;
    width: 100%;
    padding: 0.6rem 1rem;
    border-radius: 9px;
    border: none;
    background: linear-gradient(135deg, #0c2a40 0%, #0e3555 100%);
    border: 1px solid #1a4a6e;
    color: #7dd3f8 !important;
    font-family: var(--font-sub) !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    cursor: pointer;
    text-align: center;
    transition: all .2s ease;
}

.btn-scan:hover {
    background: linear-gradient(135deg, #103a55 0%, #134570 100%);
    border-color: #2a6898;
    color: #b0e4fc !important;
    box-shadow: 0 4px 20px rgba(56,189,248,0.18);
}

/* ── Secondary action button (RESCUE) ────── */
.btn-rescue {
    display: block;
    width: 100%;
    padding: 0.6rem 1rem;
    border-radius: 9px;
    background: linear-gradient(135deg, #2a1a04 0%, #3a2306 100%);
    border: 1px solid #5a3810;
    color: #fcd08a !important;
    font-family: var(--font-sub) !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    cursor: pointer;
    text-align: center;
    transition: all .2s ease;
}

.btn-rescue:hover {
    background: linear-gradient(135deg, #3a2508 0%, #4e3008 100%);
    border-color: #7a5018;
    color: #ffe0a0 !important;
    box-shadow: 0 4px 20px rgba(251,191,36,0.15);
}

/* ── Active/busy state on buttons ─────────── */
.btn-busy {
    opacity: 0.65 !important;
    cursor: not-allowed !important;
    animation: none !important;
}

/* ══════════════════════════════════════════════
   PROGRESS STEPS  (live feedback panel)
══════════════════════════════════════════════ */
.progress-panel {
    background: #080f18;
    border: 1px solid var(--border-bright);
    border-radius: 12px;
    padding: 1rem 1.1rem;
    margin-top: 0.5rem;
}

.progress-panel-title {
    font-family: var(--font-sub);
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--text-faint);
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.progress-panel-title .blink {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent-blue);
    animation: blink 1s step-start infinite;
    flex-shrink: 0;
}

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

.step-row {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.4rem 0;
    border-bottom: 1px solid #0d1a28;
    font-family: var(--font-body);
    font-size: 0.76rem;
}

.step-row:last-child { border-bottom: none; }

.step-icon-done { font-size: 0.85rem; flex-shrink: 0; margin-top: 1px; }
.step-icon-active {
    width: 14px; height: 14px;
    border: 2px solid var(--accent-blue);
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin .7s linear infinite;
    flex-shrink: 0;
    margin-top: 2px;
}

@keyframes spin { to { transform: rotate(360deg); } }

.step-icon-pending { font-size: 0.85rem; flex-shrink: 0; opacity: .25; margin-top: 1px; }

.step-label-done   { color: var(--accent-green); font-weight: 500; }
.step-label-active { color: var(--text-primary); font-weight: 600; }
.step-label-pending{ color: var(--text-faint); }

.step-sub {
    font-size: 0.67rem;
    color: var(--text-faint);
    font-family: var(--font-mono);
    line-height: 1.3;
}


/* ══════════════════════════════════════════════
   CONFIRMATION BANNER  (main area)
══════════════════════════════════════════════ */
.confirm-banner {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: #071a10;
    border: 1px solid rgba(52,211,153,.25);
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 1.5rem;
    position: relative;
    animation: slideIn .35s ease;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(-10px); }
    to   { opacity: 1; transform: translateY(0); }
}

.confirm-banner-icon { font-size: 1.8rem; flex-shrink: 0; }

.confirm-banner-body { flex: 1; }

.confirm-banner-title {
    font-family: var(--font-sub);
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--accent-green);
    margin-bottom: 0.2rem;
}

.confirm-banner-sub {
    font-family: var(--font-body);
    font-size: 0.78rem;
    color: #5a8a70;
}

.confirm-banner-time {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    color: var(--text-faint);
    align-self: flex-start;
}

/* warn banner (no files) */
.warn-banner {
    background: #1a1400;
    border: 1px solid rgba(251,191,36,.2);
}

.warn-banner .confirm-banner-title { color: var(--accent-amber); }
.warn-banner .confirm-banner-sub   { color: #7a6520; }

/* active scan banner */
.active-banner {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: #04121e;
    border: 1px solid rgba(56,189,248,.2);
    border-radius: 14px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.5rem;
    animation: pulse-border 2s ease-in-out infinite;
}

@keyframes pulse-border {
    0%,100% { border-color: rgba(56,189,248,.2); }
    50%      { border-color: rgba(56,189,248,.5); }
}

.active-banner-spinner {
    width: 22px; height: 22px;
    border: 2.5px solid rgba(56,189,248,.25);
    border-top-color: #38bdf8;
    border-radius: 50%;
    animation: spin .8s linear infinite;
    flex-shrink: 0;
}

.active-banner-text {
    font-family: var(--font-sub);
    font-size: 0.88rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--accent-blue);
}

.active-banner-sub {
    font-family: var(--font-body);
    font-size: 0.74rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}


/* ══════════════════════════════════════════════
   HERO HEADER
══════════════════════════════════════════════ */
.hero-wrap {
    position: relative;
    padding: 3rem 0 2.2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
    overflow: hidden;
}

.hero-wrap::before {
    content: '';
    position: absolute; inset: 0;
    background-image:
        linear-gradient(var(--border) 1px, transparent 1px),
        linear-gradient(90deg, var(--border) 1px, transparent 1px);
    background-size: 40px 40px;
    opacity: 0.18;
    pointer-events: none;
}

.hero-wrap::after {
    content: '';
    position: absolute;
    top: -60px; right: -80px;
    width: 380px; height: 380px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(56,189,248,0.12) 0%, transparent 65%);
    pointer-events: none;
}

.hero-eyebrow {
    font-family: var(--font-sub);
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--accent-blue);
    opacity: 0.8;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.hero-eyebrow::before {
    content: '';
    display: inline-block;
    width: 28px; height: 1.5px;
    background: var(--accent-blue);
    opacity: 0.6;
}

.hero-title {
    font-family: var(--font-display);
    font-size: clamp(3.8rem, 7vw, 6rem);
    font-weight: 400;
    letter-spacing: 3px;
    line-height: 0.92;
    color: var(--text-primary);
    margin: 0 0 0.6rem;
    text-transform: uppercase;
    position: relative;
    z-index: 1;
}

.hero-title .accent-word {
    background: linear-gradient(110deg, var(--accent-cyan) 0%, var(--accent-blue) 45%, var(--accent-indigo) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-tagline {
    font-family: var(--font-sub);
    font-size: clamp(1.05rem, 2.2vw, 1.45rem);
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin: 0.8rem 0 0;
    position: relative;
    z-index: 1;
    background: linear-gradient(90deg, var(--text-muted) 0%, #9ab8d4 30%, var(--accent-blue) 50%, #9ab8d4 70%, var(--text-muted) 100%);
    background-size: 250% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 5s linear infinite;
}

@keyframes shimmer {
    0%   { background-position: 200% center; }
    100% { background-position: -200% center; }
}

.hero-meta {
    font-family: var(--font-sub);
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: var(--text-faint);
    margin-top: 1.4rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    position: relative;
    z-index: 1;
}

.hero-meta span { color: var(--text-muted); }


/* ══════════════════════════════════════════════
   STATUS BADGE
══════════════════════════════════════════════ */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.45rem 1.1rem;
    border-radius: 99px;
    font-family: var(--font-sub);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}

.status-active   { background: rgba(52,211,153,.07);  border: 1px solid rgba(52,211,153,.2);  color: var(--accent-green); }
.status-scanning { background: rgba(251,191, 36,.07); border: 1px solid rgba(251,191, 36,.2); color: var(--accent-amber); }
.status-rescue   { background: rgba(56, 189,248,.07); border: 1px solid rgba(56,189,248,.2);  color: var(--accent-blue);  }

.pulse {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
    animation: pulse-dot 1.9s ease-in-out infinite;
}

@keyframes pulse-dot {
    0%,100% { opacity: 1; transform: scale(1);   }
    50%      { opacity: .35; transform: scale(.65); }
}


/* ══════════════════════════════════════════════
   KPI CARDS
══════════════════════════════════════════════ */
.kpi-card {
    background: linear-gradient(145deg, var(--bg-card) 0%, #0b1520 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem 1.7rem 1.3rem;
    position: relative;
    overflow: hidden;
    transition: border-color .22s ease, transform .18s ease, box-shadow .22s ease;
    margin-bottom: 1rem;
    cursor: default;
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent, linear-gradient(90deg, var(--accent-blue), var(--accent-indigo)));
}

.kpi-card::after {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,.015) 50%, transparent 60%);
    opacity: 0;
    transition: opacity .3s ease;
}

.kpi-card:hover { border-color: var(--border-bright); transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,.4); }
.kpi-card:hover::after { opacity: 1; }

.kpi-icon  { font-size: 1.15rem; margin-bottom: 0.7rem; display: block; opacity: .8; }

.kpi-value {
    font-family: var(--font-display);
    font-size: 2.8rem;
    font-weight: 400;
    letter-spacing: 1px;
    color: var(--text-primary);
    line-height: 1;
    margin-bottom: 0.3rem;
}

.kpi-label {
    font-family: var(--font-sub);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text-muted);
}

.kpi-delta {
    font-family: var(--font-body);
    font-size: 0.76rem;
    font-weight: 500;
    color: var(--accent-green);
    margin-top: 0.55rem;
}


/* ══════════════════════════════════════════════
   SECTION TITLE
══════════════════════════════════════════════ */
.section-title {
    font-family: var(--font-sub);
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 3.5px;
    color: var(--text-muted);
    margin: 2.2rem 0 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border-bright) 0%, transparent 100%);
}


/* ══════════════════════════════════════════════
   CATEGORY PILLS
══════════════════════════════════════════════ */
.cat-pill-row { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-bottom: 1.8rem; }

.cat-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 99px;
    padding: 0.38rem 1rem;
    font-family: var(--font-sub);
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #6a8daa;
    transition: border-color .2s ease, background .2s ease;
}

.cat-pill:hover { border-color: var(--border-bright); background: #111e2e; }
.cat-pill .dot  { width: 6px; height: 6px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.cat-pill strong{ color: var(--text-primary); font-weight: 700; }
.cat-pill .pct  { opacity: .4; font-size: .7rem; }


/* ══════════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #08101a !important;
    border-right: 1px solid #111e2e !important;
}

[data-testid="stSidebar"] .block-container { padding: 1.8rem 1.1rem !important; }

.sidebar-brand {
    font-family: var(--font-display);
    font-size: 1.6rem;
    letter-spacing: 3px;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.15rem;
    line-height: 1;
}

.sidebar-sub {
    font-family: var(--font-sub);
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--text-faint);
    margin-bottom: 1.8rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #0f1e2d;
}

.sidebar-section {
    font-family: var(--font-sub);
    font-size: 0.62rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2.8px;
    color: var(--text-faint);
    margin: 1.6rem 0 0.7rem;
}


/* ── Streamlit button overrides ────────────── */
.stButton > button {
    background: linear-gradient(135deg, #0c2a40 0%, #0e3555 100%) !important;
    border: 1px solid #1a4a6e !important;
    color: #7dd3f8 !important;
    border-radius: 10px !important;
    font-family: var(--font-sub) !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.2rem !important;
    transition: all .2s ease !important;
    box-shadow: none !important;
    width: 100%;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #103a55 0%, #134570 100%) !important;
    border-color: #2a6898 !important;
    color: #b0e4fc !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(56,189,248,.12) !important;
}

/* rescue button override via class trick */
div[data-testid="column"]:nth-child(2) .stButton > button {
    background: linear-gradient(135deg, #2a1a04 0%, #3a2306 100%) !important;
    border-color: #5a3810 !important;
    color: #fcd08a !important;
}

div[data-testid="column"]:nth-child(2) .stButton > button:hover {
    background: linear-gradient(135deg, #3a2508 0%, #4e3008 100%) !important;
    border-color: #7a5018 !important;
    color: #ffe0a0 !important;
    box-shadow: 0 6px 20px rgba(251,191,36,.12) !important;
}

/* ── Input, multiselect, toggle, radio ────── */
.stTextInput input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
    font-size: 0.82rem !important;
}

.stMultiSelect > div > div {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    border-radius: 9px !important;
}

.stToggle label { color: var(--text-muted) !important; font-family: var(--font-sub) !important; font-size: 0.8rem !important; letter-spacing:.5px !important; }
.stRadio  label { color: var(--text-muted) !important; font-family: var(--font-sub) !important; font-size: 0.8rem !important; }

/* ── Dataframe ────────────────────────────── */
.stDataFrame { border: 1px solid var(--border) !important; border-radius: 12px !important; overflow: hidden; }
[data-testid="stDataFrame"] table { font-family: var(--font-mono) !important; font-size: 0.76rem !important; }

/* ── Expander ─────────────────────────────── */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-muted) !important;
    font-family: var(--font-sub) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: .5px !important;
}

/* ── Alerts ───────────────────────────────── */
.stSuccess { background: rgba(52,211,153,.05) !important; border: 1px solid rgba(52,211,153,.12) !important; }
.stWarning { background: rgba(251,191, 36,.05) !important; border: 1px solid rgba(251,191, 36,.12) !important; }
.stInfo    { background: rgba(56, 189,248,.05) !important; border: 1px solid rgba(56, 189,248,.12) !important; }

hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

/* Progress bar */
.stProgress > div > div > div { background: linear-gradient(90deg,#38bdf8,#818cf8) !important; border-radius: 99px !important; }
.stProgress > div > div { background: #0c1a28 !important; border-radius: 99px !important; }


/* ══════════════════════════════════════════════
   FOOTER
══════════════════════════════════════════════ */
.footer {
    margin-top: 4rem;
    padding: 1.5rem 0 0;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.footer-left { display: flex; align-items: baseline; gap: 0.8rem; }

.footer-brand {
    font-family: var(--font-display);
    font-size: 1.1rem;
    letter-spacing: 3px;
    color: var(--text-faint);
}

.footer-tagline {
    font-family: var(--font-sub);
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-faint);
    opacity: .7;
}

.footer-meta {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    color: var(--text-faint);
}

</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HELPER FUNCTIONS  (unchanged logic)
# ─────────────────────────────────────────────

@st.cache_data(ttl=10)
def fetch_data() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query("SELECT * FROM history ORDER BY id DESC", conn)
    except Exception:
        return pd.DataFrame()


def dot_color(i: int) -> str:
    c = ["#38bdf8","#818cf8","#34d399","#fbbf24","#f472b6","#22d3ee"]
    return c[i % len(c)]


def render_progress_panel(steps: list, current_step: int, op_color: str = "#38bdf8") -> str:
    """Build HTML for the step-by-step progress panel."""
    rows = ""
    for idx, (icon, label, sub) in enumerate(steps):
        if idx < current_step:
            # completed
            rows += f"""
            <div class="step-row">
                <span class="step-icon-done">✅</span>
                <div>
                    <div class="step-label-done">{label}</div>
                    <div class="step-sub">{sub}</div>
                </div>
            </div>"""
        elif idx == current_step:
            # active
            rows += f"""
            <div class="step-row">
                <div class="step-icon-active"></div>
                <div>
                    <div class="step-label-active">{label}</div>
                    <div class="step-sub" style="color:#2a5070;">{sub}</div>
                </div>
            </div>"""
        else:
            # pending
            rows += f"""
            <div class="step-row">
                <span class="step-icon-pending">{icon}</span>
                <div>
                    <div class="step-label-pending">{label}</div>
                </div>
            </div>"""

    pct = int((current_step / len(steps)) * 100)
    return f"""
    <div class="progress-panel">
        <div class="progress-panel-title">
            <span class="blink" style="background:{op_color};"></span>
            Live Progress
        </div>
        {rows}
        <div style="margin-top:0.8rem;background:#0c1a28;border-radius:99px;height:4px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{op_color},#818cf8);
                        border-radius:99px;transition:width .3s ease;"></div>
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
                    color:#2a4a65;margin-top:0.4rem;text-align:right;">{pct}% complete</div>
    </div>"""


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────

is_scanning = st.session_state.op_status == "scanning"
is_rescuing = st.session_state.op_status == "rescuing"
is_busy     = is_scanning or is_rescuing

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">⚡ FILEFLOW</div>
    <div class="sidebar-sub">Intelligent Automation Hub</div>
    """, unsafe_allow_html=True)

    # ── OPERATION CARDS ───────────────────────
    st.markdown('<div class="sidebar-section">Operations</div>', unsafe_allow_html=True)

    # ── Surface Scan Card ─────────────────────
    st.markdown("""
    <div class="op-card op-card-scan">
        <span class="op-card-icon">🔍</span>
        <div class="op-card-title">Surface Scan</div>
        <div class="op-card-desc">Scans only the root folder and auto-organises all loose files into the right categories.</div>
    </div>
    """, unsafe_allow_html=True)

    scan_label = "⏳  Scanning Files…" if is_scanning else "🔍  Scan & Detect Files"
    scan_btn = st.button(
        scan_label,
        key="btn_scan",
        use_container_width=True,
        disabled=is_busy,
    )

    st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)

    # ── Deep Rescue Card ──────────────────────
    st.markdown("""
    <div class="op-card op-card-rescue">
        <span class="op-card-icon">🚜</span>
        <div class="op-card-title">Deep Rescue</div>
        <div class="op-card-desc">Dives into every sub-folder, finds misplaced files and rebuilds a clean directory structure.</div>
    </div>
    """, unsafe_allow_html=True)

    rescue_label = "⏳  Organising Files…" if is_rescuing else "🚜  Organise & Fix Files"
    rescue_btn = st.button(
        rescue_label,
        key="btn_rescue",
        use_container_width=True,
        disabled=is_busy,
    )

    # ── Button Logic (unchanged core) ─────────
    if scan_btn and not is_busy:
        SCAN_FLAG.touch()
        st.session_state.op_status = "scanning"
        st.session_state.op_step   = 0
        st.session_state.op_ts     = datetime.now().strftime("%H:%M:%S")
        st.rerun()

    if rescue_btn and not is_busy:
        RESCUE_FLAG.touch()
        st.session_state.op_status = "rescuing"
        st.session_state.op_step   = 0
        st.session_state.op_ts     = datetime.now().strftime("%H:%M:%S")
        st.rerun()

    # ── Live Progress Panel ───────────────────
    if is_scanning:
        step = st.session_state.op_step
        st.markdown(render_progress_panel(SCAN_STEPS, step, "#38bdf8"), unsafe_allow_html=True)

        # advance step or complete
        if SCAN_FLAG.exists():
            if step < len(SCAN_STEPS) - 1:
                time.sleep(0.9)
                st.session_state.op_step += 1
            else:
                time.sleep(0.9)
            st.rerun()
        else:
            # flag was cleared by backend → done
            st.session_state.op_status = "scan_done"
            st.session_state.op_step   = 0
            st.rerun()

    elif is_rescuing:
        step = st.session_state.op_step
        st.markdown(render_progress_panel(RESCUE_STEPS, step, "#fbbf24"), unsafe_allow_html=True)

        if RESCUE_FLAG.exists():
            if step < len(RESCUE_STEPS) - 1:
                time.sleep(0.9)
                st.session_state.op_step += 1
            else:
                time.sleep(0.9)
            st.rerun()
        else:
            st.session_state.op_status = "rescue_done"
            st.session_state.op_step   = 0
            st.rerun()

    # ── Filters ───────────────────────────────
    st.markdown('<div class="sidebar-section">Filters</div>', unsafe_allow_html=True)

    raw_data = fetch_data()
    all_categories = []
    if not raw_data.empty and 'destination' in raw_data.columns:
        all_categories = sorted(raw_data['destination'].unique().tolist())

    category_filter = st.multiselect(
        "Category",
        options=all_categories,
        default=[],
        placeholder="All categories",
        label_visibility="collapsed",
    )

    date_range = None
    if not raw_data.empty and 'timestamp' in raw_data.columns:
        try:
            raw_data['timestamp'] = pd.to_datetime(raw_data['timestamp'])
            mn, mx = raw_data['timestamp'].min().date(), raw_data['timestamp'].max().date()
            date_range = st.date_input(
                "Date Range", value=(mn, mx),
                min_value=mn, max_value=mx,
                label_visibility="collapsed",
            )
        except Exception:
            pass

    # ── Display ───────────────────────────────
    st.markdown('<div class="sidebar-section">Display</div>', unsafe_allow_html=True)
    auto_refresh = st.toggle("Auto-Refresh (15s)", value=True)
    show_raw     = st.toggle("Show Log Table",     value=True)
    chart_type   = st.radio(
        "Chart Style",
        ["Horizontal Bars", "Donut Chart"],
        index=0,
        label_visibility="visible",
    )

    # ── System ────────────────────────────────
    st.markdown('<div class="sidebar-section">System</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#1e3550; line-height:2.2;">
        DB &nbsp;&nbsp;&nbsp;→ <span style="color:#2a4a65;">{DB_PATH.name}</span><br>
        Clock → <span style="color:#2a4a65;">{datetime.now().strftime('%H:%M:%S')}</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HERO HEADER
# ─────────────────────────────────────────────

hero_left, hero_right = st.columns([3, 1], gap="large")

with hero_left:
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-eyebrow">Intelligent File Automation</div>
        <h1 class="hero-title">
            Smart File<br>
            <span class="accent-word">Automation</span> Hub
        </h1>
        <p class="hero-tagline">Let the System Do the Boring Work</p>
        <div class="hero-meta">
            <span>Real-Time Monitoring</span>
            ·
            <span>Smart Categorisation</span>
            ·
            <span>One-Click Rescue</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with hero_right:
    st.markdown("<div style='padding-top:3.5rem;'></div>", unsafe_allow_html=True)
    if is_scanning:
        st.markdown('<div class="status-badge status-scanning"><span class="pulse"></span>Surface Scan Running</div>', unsafe_allow_html=True)
    elif is_rescuing:
        st.markdown('<div class="status-badge status-rescue"><span class="pulse"></span>Deep Rescue Active</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge status-active"><span class="pulse"></span>System Online</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:1rem;background:var(--bg-card);border:1px solid var(--border);
                border-radius:12px;padding:0.9rem 1.1rem;">
        <div style="font-family:'Rajdhani',sans-serif;font-size:0.6rem;letter-spacing:2px;
                    text-transform:uppercase;color:var(--text-faint);margin-bottom:0.3rem;">Last Refresh</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:1rem;color:#38bdf8;letter-spacing:1px;">
            {datetime.now().strftime('%H:%M:%S')}
        </div>
        <div style="font-family:'Rajdhani',sans-serif;font-size:0.65rem;color:var(--text-faint);margin-top:0.2rem;">
            {datetime.now().strftime('%d %b %Y')}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  OPERATION FEEDBACK BANNERS  (main area)
# ─────────────────────────────────────────────

data = fetch_data()

# Active operation → animated progress banner in main area
if is_scanning:
    current_step = st.session_state.op_step
    steps_done   = current_step
    step_label   = SCAN_STEPS[min(current_step, len(SCAN_STEPS)-1)][1]
    pct          = int((steps_done / len(SCAN_STEPS)) * 100)
    st.markdown(f"""
    <div class="active-banner">
        <div class="active-banner-spinner"></div>
        <div>
            <div class="active-banner-text">🔍 Surface Scan In Progress</div>
            <div class="active-banner-sub">{step_label} &nbsp;·&nbsp; Started at {st.session_state.op_ts or '—'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(max(pct, 5))

elif is_rescuing:
    current_step = st.session_state.op_step
    steps_done   = current_step
    step_label   = RESCUE_STEPS[min(current_step, len(RESCUE_STEPS)-1)][1]
    pct          = int((steps_done / len(RESCUE_STEPS)) * 100)
    st.markdown(f"""
    <div class="active-banner">
        <div class="active-banner-spinner" style="border-top-color:#fbbf24;"></div>
        <div>
            <div class="active-banner-text" style="color:#fbbf24;">🚜 Deep Rescue In Progress</div>
            <div class="active-banner-sub">{step_label} &nbsp;·&nbsp; Started at {st.session_state.op_ts or '—'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(max(pct, 5))

# Completion banners
elif st.session_state.op_status == "scan_done":
    file_count = len(data) if not data.empty else 0
    if file_count > 0:
        st.markdown(f"""
        <div class="confirm-banner">
            <div class="confirm-banner-icon">✅</div>
            <div class="confirm-banner-body">
                <div class="confirm-banner-title">Surface Scan Completed Successfully</div>
                <div class="confirm-banner-sub">
                    All root-level files have been scanned and classified into <strong style="color:#5a9a78;">{file_count:,}</strong> total records.
                    Dashboard updated below.
                </div>
            </div>
            <div class="confirm-banner-time">{st.session_state.op_ts or ''}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="confirm-banner warn-banner">
            <div class="confirm-banner-icon">⚠️</div>
            <div class="confirm-banner-body">
                <div class="confirm-banner-title">Scan Complete — No Files Found</div>
                <div class="confirm-banner-sub">
                    The root directory appears to be empty or already organised. Nothing was moved.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    col_dismiss, _ = st.columns([1, 4])
    with col_dismiss:
        if st.button("✕  Dismiss", key="dismiss_scan"):
            st.session_state.op_status = "idle"
            st.rerun()

elif st.session_state.op_status == "rescue_done":
    file_count = len(data) if not data.empty else 0
    if file_count > 0:
        st.markdown(f"""
        <div class="confirm-banner">
            <div class="confirm-banner-icon">🎉</div>
            <div class="confirm-banner-body">
                <div class="confirm-banner-title">Files Organised Successfully</div>
                <div class="confirm-banner-sub">
                    Deep rescue completed. All sub-folders have been processed. Total log entries: <strong style="color:#5a9a78;">{file_count:,}</strong>.
                    Your directory is now clean.
                </div>
            </div>
            <div class="confirm-banner-time">{st.session_state.op_ts or ''}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="confirm-banner warn-banner">
            <div class="confirm-banner-icon">⚠️</div>
            <div class="confirm-banner-body">
                <div class="confirm-banner-title">Rescue Complete — Nothing to Fix</div>
                <div class="confirm-banner-sub">
                    No misplaced files were found. Your folders are already well-organised.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    col_dismiss, _ = st.columns([1, 4])
    with col_dismiss:
        if st.button("✕  Dismiss", key="dismiss_rescue"):
            st.session_state.op_status = "idle"
            st.rerun()


# ─────────────────────────────────────────────
#  DATA PROCESSING
# ─────────────────────────────────────────────

filtered_data = data.copy()
if not filtered_data.empty:
    if category_filter:
        filtered_data = filtered_data[filtered_data['destination'].isin(category_filter)]
    if date_range and 'timestamp' in filtered_data.columns and len(date_range) == 2:
        try:
            filtered_data['timestamp'] = pd.to_datetime(filtered_data['timestamp'])
            filtered_data = filtered_data[
                (filtered_data['timestamp'].dt.date >= date_range[0]) &
                (filtered_data['timestamp'].dt.date <= date_range[1])
            ]
        except Exception:
            pass


# ─────────────────────────────────────────────
#  KPI METRICS ROW
# ─────────────────────────────────────────────

st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

total_files  = len(data)                          if not data.empty else 0
active_cats  = data['destination'].nunique()       if not data.empty else 0
recent_count = 0
db_size_kb   = round(DB_PATH.stat().st_size / 1024, 1) if DB_PATH.exists() else 0

if not data.empty and 'timestamp' in data.columns:
    try:
        ts = pd.to_datetime(data['timestamp'])
        recent_count = int((ts >= pd.Timestamp.now() - pd.Timedelta(hours=24)).sum())
    except Exception:
        pass

kpi_specs = [
    ("⚡", str(total_files),  "Files Organised",   "All time",         "linear-gradient(90deg,#38bdf8,#818cf8)"),
    ("📂", str(active_cats),  "Active Buckets",     "Distinct folders", "linear-gradient(90deg,#818cf8,#f472b6)"),
    ("🕐", str(recent_count), "Last 24 Hours",      "Recent activity",  "linear-gradient(90deg,#34d399,#22d3ee)"),
    ("💾", f"{db_size_kb}KB", "Database Size",      "automation.db",    "linear-gradient(90deg,#fbbf24,#f472b6)"),
]

for col, (icon, val, label, sub, grad) in zip(st.columns(4), kpi_specs):
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="--accent:{grad};">
            <span class="kpi-icon">{icon}</span>
            <div class="kpi-value">{val}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-delta">{sub}</div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN CONTENT
# ─────────────────────────────────────────────

if not filtered_data.empty:

    counts = filtered_data['destination'].value_counts().reset_index()
    counts.columns = ['Category', 'Count']

    # ── Category Pills ────────────────────────
    st.markdown('<div class="section-title">Category Breakdown</div>', unsafe_allow_html=True)

    pills_html = '<div class="cat-pill-row">'
    for i, row in counts.iterrows():
        pct   = round(row['Count'] / counts['Count'].sum() * 100, 1)
        label = row['Category'].replace('_', ' ').title()
        pills_html += f"""
        <div class="cat-pill">
            <span class="dot" style="background:{dot_color(i)};box-shadow:0 0 6px {dot_color(i)}60;"></span>
            {label}
            <strong>{row['Count']}</strong>
            <span class="pct">{pct}%</span>
        </div>"""
    pills_html += '</div>'
    st.markdown(pills_html, unsafe_allow_html=True)

    # ── Chart + Stats ─────────────────────────
    st.markdown('<div class="section-title">Volume Distribution</div>', unsafe_allow_html=True)

    chart_col, info_col = st.columns([3, 1], gap="medium")

    with chart_col:
        if chart_type == "Horizontal Bars":
            chart = (
                alt.Chart(counts)
                .mark_bar(cornerRadiusTopRight=9, cornerRadiusBottomRight=9)
                .encode(
                    x=alt.X('Count:Q', title='Files Organised',
                             axis=alt.Axis(grid=True, gridColor='#0f1e2d', gridOpacity=1,
                                           labelColor='#3d5a78', titleColor='#3d5a78',
                                           labelFont='JetBrains Mono', labelFontSize=11,
                                           tickColor='transparent')),
                    y=alt.Y('Category:N', title=None, sort='-x',
                             axis=alt.Axis(labelColor='#8bacc8', labelFontSize=12,
                                           labelFont='Figtree', tickColor='transparent')),
                    color=alt.Color('Count:Q',
                                    scale=alt.Scale(range=['#162235','#38bdf8']),
                                    legend=None),
                    tooltip=[alt.Tooltip('Category:N', title='Category'),
                              alt.Tooltip('Count:Q',    title='Files')],
                )
                .properties(height=max(200, len(counts) * 54))
                .configure_view(strokeOpacity=0, fill='#0c1220')
                .configure_axis(domainColor='#162235')
            )
            st.altair_chart(chart, use_container_width=True)

        else:
            arc = (
                alt.Chart(counts)
                .mark_arc(innerRadius=75, outerRadius=135, padAngle=0.028)
                .encode(
                    theta=alt.Theta('Count:Q'),
                    color=alt.Color('Category:N',
                                    scale=alt.Scale(range=['#38bdf8','#818cf8','#34d399',
                                                           '#fbbf24','#f472b6','#22d3ee']),
                                    legend=alt.Legend(labelColor='#8bacc8', labelFont='Figtree',
                                                      titleColor='#3d5a78', orient='right')),
                    tooltip=[alt.Tooltip('Category:N', title='Category'),
                              alt.Tooltip('Count:Q',    title='Files')],
                )
                .properties(height=310)
                .configure_view(strokeOpacity=0, fill='#0c1220')
            )
            st.altair_chart(arc, use_container_width=True)

    with info_col:
        top_cat = counts.iloc[0] if not counts.empty else None
        if top_cat is not None:
            st.markdown(f"""
            <div class="kpi-card" style="--accent:linear-gradient(90deg,#38bdf8,#818cf8);">
                <div class="kpi-label" style="margin-bottom:0.6rem;">Top Bucket</div>
                <div style="font-family:'Bebas Neue',sans-serif;font-size:1.45rem;letter-spacing:1.5px;
                            color:var(--text-primary);line-height:1.15;margin-bottom:0.5rem;">
                    {top_cat['Category'].replace('_',' ').upper()}
                </div>
                <div class="kpi-value" style="font-size:2.2rem;">{top_cat['Count']}</div>
                <div class="kpi-label">files</div>
            </div>
            """, unsafe_allow_html=True)

        total = counts['Count'].sum()
        avg   = round(counts['Count'].mean(), 1) if not counts.empty else 0
        st.markdown(f"""
        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;
                    padding:1rem 1.2rem;margin-top:0.8rem;line-height:2.3;">
            <div style="font-family:'Rajdhani',sans-serif;font-size:0.66rem;font-weight:700;
                        letter-spacing:2px;text-transform:uppercase;color:var(--text-faint);margin-bottom:.3rem;">
                Summary
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:var(--text-muted);">
                Total &nbsp;→ <strong style="color:#8bacc8;">{total}</strong><br>
                Avg/cat → <strong style="color:#8bacc8;">{avg}</strong><br>
                Buckets → <strong style="color:#8bacc8;">{len(counts)}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── History Log ───────────────────────────
    if show_raw:
        st.markdown('<div class="section-title">Organisation Log</div>', unsafe_allow_html=True)

        s_col, e_col = st.columns([4, 1])
        with s_col:
            search_query = st.text_input(
                "Search",
                placeholder="Filter by filename, category …",
                label_visibility="collapsed",
            )
        with e_col:
            st.download_button(
                label="⬇ Export CSV",
                data=filtered_data.to_csv(index=False),
                file_name=f"fileflow_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        display_df = filtered_data.copy()
        if search_query:
            mask = display_df.apply(
                lambda c: c.astype(str).str.contains(search_query, case=False, na=False)
            ).any(axis=1)
            display_df = display_df[mask]

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=340)
        st.markdown(
            f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:0.68rem;"
            f"color:var(--text-faint);margin-top:.4rem;'>"
            f"Showing {len(display_df):,} / {len(data):,} records</div>",
            unsafe_allow_html=True,
        )

    # ── Advanced Stats ────────────────────────
    with st.expander("🔬  Advanced Statistics", expanded=False):
        adv1, adv2 = st.columns(2)

        with adv1:
            if 'timestamp' in filtered_data.columns:
                try:
                    ts_df = filtered_data.copy()
                    ts_df['timestamp'] = pd.to_datetime(ts_df['timestamp'])
                    ts_df['date'] = ts_df['timestamp'].dt.date
                    daily = ts_df.groupby('date').size().reset_index(name='count')
                    daily['date'] = pd.to_datetime(daily['date'])

                    line_chart = (
                        alt.Chart(daily)
                        .mark_area(
                            line={'color': '#38bdf8', 'strokeWidth': 2},
                            color=alt.Gradient(
                                gradient='linear',
                                stops=[alt.GradientStop(color='rgba(56,189,248,0.3)', offset=0),
                                       alt.GradientStop(color='rgba(56,189,248,0)',   offset=1)],
                                x1=0, x2=0, y1=1, y2=0,
                            ),
                        )
                        .encode(
                            x=alt.X('date:T', title='Date',
                                    axis=alt.Axis(labelColor='#3d5a78', gridColor='#0f1e2d',
                                                  titleColor='#3d5a78', labelFont='JetBrains Mono')),
                            y=alt.Y('count:Q', title='Files',
                                    axis=alt.Axis(labelColor='#3d5a78', gridColor='#0f1e2d',
                                                  titleColor='#3d5a78', labelFont='JetBrains Mono')),
                            tooltip=['date:T','count:Q'],
                        )
                        .properties(height=200, title=alt.Title('Daily Activity', color='#4a6880'))
                        .configure_view(strokeOpacity=0, fill='#0c1220')
                    )
                    st.altair_chart(line_chart, use_container_width=True)
                except Exception:
                    st.info("Timestamp data not parseable for timeline view.")

        with adv2:
            st.dataframe(
                counts.rename(columns={'Category':'Bucket','Count':'Files'})
                      .assign(Share=lambda d: (d['Files']/d['Files'].sum()*100).round(1).astype(str)+'%'),
                use_container_width=True,
                hide_index=True,
                height=210,
            )

# ── Empty State ───────────────────────────────
else:
    if not is_busy:
        st.markdown("""
        <div style="text-align:center;padding:6rem 2rem;
                    border:1px dashed #162235;border-radius:18px;margin:2rem 0;">
            <div style="font-size:3.5rem;margin-bottom:1.2rem;opacity:.25;">📁</div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;letter-spacing:3px;
                        color:#1e3550;margin-bottom:.6rem;">NO DATA YET</div>
            <div style="font-family:'Rajdhani',sans-serif;font-size:.82rem;font-weight:600;
                        letter-spacing:1.5px;text-transform:uppercase;color:#162235;">
                Use <strong style="color:#2a4060;">Scan &amp; Detect Files</strong> or
                <strong style="color:#2a4060;">Organise &amp; Fix Files</strong> to begin.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────

st.markdown(f"""
<div class="footer">
    <div class="footer-left">
        <span class="footer-brand">⚡ FILEFLOW</span>
        <span class="footer-tagline">Let the System Do the Boring Work</span>
    </div>
    <div class="footer-meta">
        {DB_PATH.name} &nbsp;·&nbsp; {datetime.now().strftime('%d %b %Y, %H:%M')}
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  AUTO-REFRESH  (unchanged logic)
# ─────────────────────────────────────────────

if auto_refresh and not is_busy:
    time.sleep(15)
    st.rerun()