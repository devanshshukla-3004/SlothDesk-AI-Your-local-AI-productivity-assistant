from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from slothdesk.ai_engine import DEFAULT_MODEL, ollama_status, suggest_organization
from slothdesk.organizer import apply_plan, build_plan, duplicate_groups, safe_name, scan_directory

st.set_page_config(page_title="SlothDesk AI", page_icon="🦥", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root {
  color-scheme: light;
  --sd-lime: #c8f26b;
  --sd-bg: #e5ebe1;
  --sd-surface: #e8eee5;
  --sd-input: #f0f4ec;
  --sd-text: #26382d;
  --sd-muted: #526557;
  --sd-border: #bdcbbb;
  --sd-sidebar: #172b21;
}
.stApp { background: var(--sd-bg) !important; color: var(--sd-text) !important; }
[data-testid="stHeader"] { background: var(--sd-bg) !important; height: 3rem !important; }
[data-testid="stMainBlockContainer"], .block-container {
  padding-top: 4rem !important; padding-bottom: 3rem !important;
  max-width: 1500px;
}
/* Sidebar scroll and bottom breathing room */
[data-testid="stSidebar"] { background: var(--sd-sidebar) !important; }
[data-testid="stSidebar"] > div:first-child {
  height: 100vh !important; overflow-y: auto !important;
  padding-bottom: 3.5rem !important; box-sizing: border-box !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  padding-bottom: 3.5rem !important;
}
[data-testid="stSidebar"] * { color: #d0ddd1; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] .stCaption { color: #c0cfc2 !important; }
[data-testid="stSidebar"] hr { border-color: #35483a !important; }
/* Sidebar text inputs: force readable value, caret and placeholder */
[data-testid="stSidebar"] [data-baseweb="input"] {
  background: var(--sd-input) !important; border: 1px solid var(--sd-border) !important;
  border-radius: 10px !important;
}
[data-testid="stSidebar"] [data-baseweb="input"] input {
  color: var(--sd-text) !important; -webkit-text-fill-color: var(--sd-text) !important;
  caret-color: var(--sd-text) !important; background: transparent !important;
  opacity: 1 !important;
}
[data-testid="stSidebar"] [data-baseweb="input"] input::placeholder {
  color: #637567 !important; -webkit-text-fill-color: #637567 !important; opacity: 1 !important;
}
/* Main area inputs also ignore browser/Streamlit theme text colors */
[data-testid="stMainBlockContainer"] [data-baseweb="input"] {
  background: var(--sd-input) !important; border-color: var(--sd-border) !important;
}
[data-testid="stMainBlockContainer"] [data-baseweb="input"] input {
  color: var(--sd-text) !important; -webkit-text-fill-color: var(--sd-text) !important;
  caret-color: var(--sd-text) !important; opacity: 1 !important;
}
[data-testid="stMainBlockContainer"] [data-baseweb="input"] input::placeholder {
  color: #637567 !important; -webkit-text-fill-color: #637567 !important; opacity: 1 !important;
}
/* Number input: label, typed value, +/- buttons */
[data-testid="stNumberInput"] label,
[data-testid="stNumberInput"] label p,
[data-testid="stNumberInput"] [data-testid="stWidgetLabel"] {
  color: var(--sd-text) !important; -webkit-text-fill-color: var(--sd-text) !important;
  font-weight: 650 !important;
}
[data-testid="stNumberInput"] [data-baseweb="input"] {
  background: var(--sd-input) !important; border-color: var(--sd-border) !important;
}
[data-testid="stNumberInput"] input {
  color: var(--sd-text) !important; -webkit-text-fill-color: var(--sd-text) !important;
  caret-color: var(--sd-text) !important; opacity: 1 !important;
}
[data-testid="stNumberInput"] button {
  background: #dce7d6 !important; color: var(--sd-text) !important;
  border-color: var(--sd-border) !important; opacity: 1 !important;
}
[data-testid="stNumberInput"] button svg {
  color: var(--sd-text) !important; fill: var(--sd-text) !important;
}
[data-testid="stNumberInput"] button:hover { background: #cbdcc2 !important; }
/* Disabled buttons: still legible, but visibly inactive */
.stApp button:disabled,
.stApp button[disabled],
.stApp [data-testid="stButton"] button:disabled {
  background: #d5dfd0 !important; color: #526557 !important;
  -webkit-text-fill-color: #526557 !important; border: 1px solid #b7c6b3 !important;
  opacity: .82 !important; cursor: not-allowed !important; box-shadow: none !important;
}
/* Primary active actions */
.stApp button[kind="primary"]:not(:disabled) {
  background: var(--sd-lime) !important; color: #203426 !important;
  -webkit-text-fill-color: #203426 !important; border: 1px solid #b4dc58 !important;
}
.stApp button[kind="primary"]:not(:disabled):hover { background: #d7f99a !important; }
/* Hero title: avoid overly tight text and clipping */
.hero h1 { letter-spacing: -0.02em !important; line-height: 1.08 !important; overflow-wrap: anywhere; }
/* Lime slider: Streamlit theme variable + BaseWeb thumb and rail */
.stApp { --primary-color: #c8f26b !important; accent-color: #c8f26b !important; }
[data-baseweb="slider"] [role="slider"] {
  background: #c8f26b !important; border: 2px solid #526b39 !important;
  box-shadow: 0 0 0 2px rgba(200,242,107,.22) !important;
}
[data-baseweb="slider"] [data-testid="stSliderTrack"] { background: #c8f26b !important; }
[data-baseweb="slider"] [data-testid="stSliderThumb"] { background: #c8f26b !important; }
[data-baseweb="slider"] [data-testid="stSliderTrack"] > div { background: #3f7d3a !important; }
[data-testid="stSlider"] [data-baseweb="slider"] > div > div { accent-color: #3f7d3a !important; }
/* Contrast for metric subtitles, labels, and helper copy */
.metric-sub, .metric-label, .section-label { color: #526557 !important; }
[data-testid="stCaptionContainer"], [data-testid="stMarkdownContainer"] small {
  color: #526557 !important;
}
.stApp [data-testid="stMain"] [data-testid="stWidgetLabel"], .stApp [data-testid="stMain"] [data-testid="stWidgetLabel"] p { color: var(--sd-text) !important; -webkit-text-fill-color: var(--sd-text) !important; }
.stApp [data-testid="stSidebar"] [data-testid="stWidgetLabel"], .stApp [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p, .stApp [data-testid="stSidebar"] label, .stApp [data-testid="stSidebar"] label p, .stApp [data-testid="stSidebar"] [data-testid="stCheckbox"] p, .stApp [data-testid="stSidebar"] [data-testid="stTickBarMin"], .stApp [data-testid="stSidebar"] [data-testid="stTickBarMax"], .stApp [data-testid="stSidebar"] [data-testid="stSliderThumbValue"] { color: #e8efe9 !important; -webkit-text-fill-color: #e8efe9 !important; }
/* Restore light readable helper text inside the dark sidebar */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: #c0cfc2 !important; }
/* Existing cards use sage, never pure white */
.metric-card, [data-testid="stDataFrame"], [data-testid="stExpander"] {
  background: var(--sd-surface) !important;
}
[data-testid="stDataFrame"] { border-color: var(--sd-border) !important; }
[data-testid="stExpander"] { border-color: var(--sd-border) !important; }
hr { border-color: #cbd6c8 !important; }
@media (max-width: 700px) {
  [data-testid="stMainBlockContainer"], .block-container {
    padding-top: 3rem !important; padding-bottom: 2rem !important;
  }
  [data-testid="stSidebar"] > div:first-child { padding-bottom: 3.5rem !important; }
}
/* Restore the original SlothDesk brand and hero design */
.brand-row { display:flex; align-items:center; gap:.8rem; margin:.4rem 0 .5rem; }
.brand-mark { width:42px; height:42px; border-radius:12px; background:#c8f26b; display:flex; align-items:center; justify-content:center; font-size:1.45rem; flex:0 0 42px; }
.brand-name { font-size:1.12rem; font-weight:800; color:#fff !important; letter-spacing:-.01em; line-height:1.2; }
.brand-sub { font-size:.76rem; color:#a9bcab !important; margin-top:2px; }
.side-eyebrow { font-size:.72rem; font-weight:700; letter-spacing:.14em; color:#a9bcab !important; margin:.3rem 0 .2rem; }
.hero { position:relative; overflow:hidden; border-radius:28px; background:linear-gradient(135deg,#284433 0%,#213a2d 100%); padding:2.6rem 2.8rem 2.2rem; margin-bottom:1.4rem; box-shadow:0 18px 40px rgba(23,43,33,.18); }
.hero::after { content:""; position:absolute; right:-90px; top:-130px; width:380px; height:380px; border-radius:50%; border:48px solid rgba(200,242,107,.06); pointer-events:none; }
.hero .tag { display:inline-flex; align-items:center; gap:.5rem; margin-bottom:1rem; font-size:.74rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:#c8f26b !important; }
.hero .tag .dot { width:8px; height:8px; border-radius:50%; background:#c8f26b; display:inline-block; }
.hero h1 { color:#fff !important; font-size:3.2rem !important; font-weight:800 !important; letter-spacing:-.02em !important; line-height:1.08 !important; margin:0 0 1rem !important; padding:0 !important; overflow-wrap:anywhere; }
.hero p { color:#cbd9cd !important; max-width:660px; font-size:1rem; line-height:1.7; margin:0 0 1.4rem; }
.hero-foot { display:flex; flex-wrap:wrap; gap:.6rem; }
.hero-chip { display:inline-block; padding:.45rem .85rem; border-radius:12px; font-size:.78rem; color:#dfeadf !important; background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.12); }
.metric-card { background:#e8eee5 !important; border:1px solid #bdcbbb !important; border-radius:22px !important; padding:1.3rem 1.4rem 1.2rem; min-height:130px; }
.metric-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:.7rem; }
.metric-label { font-size:.7rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:#526557 !important; }
.metric-icon { width:32px; height:32px; border-radius:10px; background:#d7e4d1; color:#3f6150 !important; display:flex; align-items:center; justify-content:center; font-size:.95rem; }
.metric-value { font-size:2.1rem; font-weight:800; line-height:1.1; color:#26382d !important; letter-spacing:-.02em; }
.metric-sub { font-size:.78rem; color:#526557 !important; margin-top:.45rem; }
.section-label { font-size:.78rem !important; font-weight:700; letter-spacing:.2em; text-transform:uppercase; color:#526557 !important; margin:.4rem 0 .3rem !important; }
.stApp [data-testid="stMain"] [data-testid="stCaptionContainer"], .stApp [data-testid="stMain"] [data-testid="stCaptionContainer"] * { color:#526557 !important; }
.stApp [data-testid="stSidebar"] [data-testid="stCaptionContainer"], .stApp [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color:#b4c5b6 !important; }
[data-baseweb="select"] > div { background:#f0f4ec !important; border-color:#bdcbbb !important; }
[data-baseweb="select"] * { color:#26382d !important; }
[data-baseweb="slider"] [role="slider"] { background:#c8f26b !important; border:2px solid #3f7d3a !important; box-shadow:0 0 0 3px rgba(200,242,107,.25) !important; }
@media (max-width:700px) { .hero { padding:1.6rem 1.3rem; } .hero h1 { font-size:2.1rem !important; } }
</style>
""", unsafe_allow_html=True)

if "files" not in st.session_state:
    st.session_state.files = []
if "plan" not in st.session_state:
    st.session_state.plan = []
if "last_results" not in st.session_state:
    st.session_state.last_results = []

with st.sidebar:
    st.markdown('<div class="brand-row"><div class="brand-mark">🦥</div><div><div class="brand-name">SlothDesk AI</div><div class="brand-sub">Your private file workspace</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-eyebrow">LOCAL-FIRST PRODUCTIVITY</div>', unsafe_allow_html=True)
    st.divider()
    folder = st.text_input("Folder to organize", value=str(Path.home() / "Downloads"), help="Only this folder will be scanned. Nothing changes until you approve a plan.")
    recursive = st.checkbox("Include subfolders", value=False)
    max_files = st.select_slider("Maximum files to scan", options=[100, 250, 500, 1000, 2000], value=500)
    st.divider()
    st.markdown("### Local AI")
    model = st.text_input("Ollama model", value=os.getenv("SLOTHDESK_OLLAMA_MODEL", DEFAULT_MODEL))
    connected, models = ollama_status()
    if connected:
        st.success("Ollama is reachable")
        if models:
            st.caption("Installed: " + ", ".join(models[:5]))
        else:
            st.caption("No models detected. Pull one with Ollama first.")
    else:
        st.info("Ollama offline — rule-based organization still works.")
    st.caption("Only filenames and extensions are sent to Ollama. File contents are not uploaded.")

st.markdown("""
<div class="hero">
  <span class="tag"><span class="dot"></span> YOUR FILES. YOUR DEVICE. YOUR CALL.</span>
  <h1>A clearer space for<br>everything you keep.</h1>
  <p>Bring order to your downloads with thoughtful file suggestions, local AI, and a review-first workflow. Nothing moves until you say so.</p>
  <div class="hero-foot"><span class="hero-chip">◉ Local by default</span><span class="hero-chip">↗ AI-powered suggestions</span><span class="hero-chip">✓ You approve every move</span></div>
</div>
""", unsafe_allow_html=True)

top1, top2, top3 = st.columns(3)
with top1:
    st.markdown('<div class="metric-card"><div class="metric-top"><div class="metric-label">Files scanned</div><div class="metric-icon">▤</div></div><div class="metric-value">' + str(len(st.session_state.files)) + '</div><div class="metric-sub">In the selected folder</div></div>', unsafe_allow_html=True)
with top2:
    total_bytes = sum(int(item.get("size_bytes", 0)) for item in st.session_state.files)
    st.markdown('<div class="metric-card"><div class="metric-top"><div class="metric-label">Space reviewed</div><div class="metric-icon">◫</div></div><div class="metric-value">' + (f"{total_bytes / (1024 * 1024):.1f} MB" if total_bytes < 1024**3 else f"{total_bytes / (1024**3):.2f} GB") + '</div><div class="metric-sub">Metadata checked locally</div></div>', unsafe_allow_html=True)
with top3:
    pending = len(st.session_state.plan)
    st.markdown('<div class="metric-card"><div class="metric-top"><div class="metric-label">Suggested actions</div><div class="metric-icon">✳</div></div><div class="metric-value">' + str(pending) + '</div><div class="metric-sub">Waiting for your review</div></div>', unsafe_allow_html=True)

st.write("")
left, right = st.columns([1, 1], gap="large")
with left:
    st.markdown('<p class="section-label">01 / Find the clutter</p>', unsafe_allow_html=True)
    st.markdown("#### Scan your workspace")
    st.write("We inspect filenames, extensions, file sizes and timestamps. File contents are not read during scanning.")
    if st.button("Scan selected folder", type="primary", use_container_width=True):
        try:
            with st.spinner("Scanning locally…"):
                st.session_state.files = scan_directory(folder, recursive=recursive, max_files=max_files)
                st.session_state.plan = []
                st.session_state.last_results = []
            st.success(f"Scanned {len(st.session_state.files)} files.")
        except (ValueError, OSError) as exc:
            st.error(str(exc))
with right:
    st.markdown('<p class="section-label">02 / Let AI help</p>', unsafe_allow_html=True)
    st.markdown("#### Get smarter suggestions")
    st.write("Use your local Ollama model to suggest a category and a clearer filename. You review every suggestion.")
    ai_limit = st.number_input("Files to ask the model about", min_value=1, max_value=30, value=10, step=1)
    if st.button("Generate local AI suggestions", use_container_width=True, disabled=not bool(st.session_state.files)):
        connected, _ = ollama_status()
        if not connected:
            st.warning("Ollama isn't responding at 127.0.0.1:11434. Start Ollama and install a model, or use the rule-based plan below.")
        else:
            updates = 0
            errors = []
            with st.spinner("Asking your local model…"):
                for item in st.session_state.files[:int(ai_limit)]:
                    try:
                        result = suggest_organization(item["name"], item["extension"], model=model)
                        item["category"] = result["category"]
                        item["suggested_name"] = safe_name(result["suggested_name"])
                        updates += 1
                    except Exception as exc:
                        errors.append(f'{item["name"]}: {exc}')
            st.session_state.plan = []
            st.success(f"Created suggestions for {updates} files.")
            if errors:
                st.warning("Some files were skipped: " + "; ".join(errors[:3]))

if st.session_state.files:
    st.write("")
    st.markdown('<p class="section-label">03 / Review</p>', unsafe_allow_html=True)
    st.markdown("#### Your workspace, at a glance")
    df = pd.DataFrame(st.session_state.files)
    display_columns = [column for column in ["name", "suggested_name", "extension", "category", "size_bytes"] if column in df.columns]
    st.dataframe(df[display_columns], use_container_width=True, hide_index=True)
    counts = df["category"].value_counts().rename_axis("Category").reset_index(name="Files")
    st.bar_chart(counts.set_index("Category"))
    with st.expander("Find exact duplicates (optional)"):
        st.caption("This reads file bytes to calculate SHA-256 hashes locally. It does not upload content.")
        if st.button("Check for identical files"):
            with st.spinner("Hashing same-size files…"):
                groups = duplicate_groups(st.session_state.files)
            if groups:
                for index, group in enumerate(groups, start=1):
                    st.write(f"**Duplicate group {index}**")
                    for item in group:
                        st.code(item)
            else:
                st.info("No exact duplicates found among the scanned files.")

    st.write("")
    st.markdown('<p class="section-label">04 / Approve changes</p>', unsafe_allow_html=True)
    st.markdown("#### Preview the organization plan")
    organize = st.toggle("Move files into category folders", value=True)
    if st.button("Build review plan", type="primary", use_container_width=True):
        st.session_state.plan = build_plan(st.session_state.files, folder, organize=organize)
    if st.session_state.plan:
        plan_df = pd.DataFrame(st.session_state.plan)
        st.dataframe(plan_df[["source", "destination", "status"]], use_container_width=True, hide_index=True)
        st.warning("Nothing has changed yet. Approval will move files on this computer. Existing destinations are never overwritten.")
        confirm = st.checkbox("I reviewed the plan and approve these file moves.")
        if st.button("Approve and apply plan", type="primary", disabled=not confirm, use_container_width=True):
            try:
                st.session_state.last_results = apply_plan(st.session_state.plan, folder)
                moved = sum(result["status"] == "moved" for result in st.session_state.last_results)
                st.session_state.plan = []
                st.success(f"Finished. {moved} file(s) moved.")
                st.rerun()
            except (ValueError, OSError) as exc:
                st.error(str(exc))
    elif st.session_state.files:
        st.caption("Build a plan to preview proposed changes before applying them.")

if st.session_state.last_results:
    st.write("")
    st.markdown('<p class="section-label">Activity / Last run</p>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(st.session_state.last_results), use_container_width=True, hide_index=True)
    csv = pd.DataFrame(st.session_state.last_results).to_csv(index=False).encode("utf-8")
    st.download_button("Download activity report (CSV)", data=csv, file_name=f"slothdesk-activity-{datetime.now():%Y%m%d-%H%M%S}.csv", mime="text/csv")

st.divider()
st.caption("SlothDesk AI • Local-first by design • Preview first, approve second. This MVP does not delete files.")
