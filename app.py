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
:root { --sd-ink:#17231e; --sd-muted:#78837d; --sd-lime:#c8f36a; --sd-paper:#f4f5f0; --sd-line:#e3e7df; --sd-white:#fff; }
html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.stApp { background:var(--sd-paper); color:var(--sd-ink); }
[data-testid="stHeader"] { background:rgba(244,245,240,.92); }
[data-testid="stMainBlockContainer"] { padding-top:1.65rem; padding-bottom:3rem; max-width:1500px; }
[data-testid="stSidebar"] { background:#17231e; border-right:1px solid #2c3932; }
[data-testid="stSidebar"] > div { padding:1.4rem 1rem; }
[data-testid="stSidebar"] * { color:#edf2e9; }
[data-testid="stSidebar"] hr { border-color:#354139; margin:1.2rem 0; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] .stCaption { color:#b4c0b7 !important; }
[data-testid="stSidebar"] input { background:#243129; border:1px solid #3c4a41; border-radius:10px; }
.brand-row { display:flex; align-items:center; gap:11px; padding:3px 0 8px; }
.brand-mark { width:39px; height:39px; display:flex; align-items:center; justify-content:center; border-radius:13px; background:var(--sd-lime); color:#17231e; font-size:23px; }
.brand-name { color:#f4f7f1; font-size:1.18rem; font-weight:850; letter-spacing:-.045em; }
.brand-sub { color:#a8b5ab; font-size:.72rem; margin-top:2px; }
.hero { position:relative; overflow:hidden; background:#17231e; border:1px solid #2b3931; border-radius:25px; padding:31px 34px 29px; color:#f5f7f2; margin:0 0 19px; box-shadow:0 12px 35px rgba(26,39,31,.07); }
.hero:after { content:""; position:absolute; width:260px; height:260px; border:1px solid rgba(200,243,106,.22); border-radius:50%; right:-60px; top:-105px; box-shadow:0 0 0 28px rgba(200,243,106,.035),0 0 0 58px rgba(200,243,106,.025); pointer-events:none; }
.hero .tag { display:inline-flex; align-items:center; gap:7px; background:rgba(200,243,106,.12); color:var(--sd-lime); border:1px solid rgba(200,243,106,.22); border-radius:999px; padding:6px 10px; font-size:.68rem; font-weight:850; letter-spacing:.1em; margin-bottom:16px; }
.hero h1 { color:#f5f7f2; font-size:clamp(2rem,3.4vw,3.25rem); line-height:1.02; letter-spacing:-.065em; font-weight:850; margin:0; max-width:650px; }
.hero p { color:#bdc8bf; font-size:.94rem; line-height:1.7; max-width:590px; margin:14px 0 0; }
.hero-foot { display:flex; flex-wrap:wrap; gap:8px; margin-top:21px; }
.hero-chip { display:inline-flex; align-items:center; gap:7px; padding:7px 10px; border-radius:9px; color:#e0e8df; background:#243129; border:1px solid #354139; font-size:.73rem; }
.dot { width:7px; height:7px; border-radius:50%; background:var(--sd-lime); display:inline-block; }
.metric-card { background:var(--sd-white); border:1px solid var(--sd-line); border-radius:17px; padding:17px 19px; min-height:104px; box-shadow:0 3px 12px rgba(24,38,29,.025); transition:transform .18s ease,border-color .18s ease; }
.metric-card:hover { transform:translateY(-2px); border-color:#cbd5c9; }
.metric-top { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.metric-label { color:var(--sd-muted); font-size:.7rem; font-weight:800; text-transform:uppercase; letter-spacing:.105em; }
.metric-icon { display:flex; align-items:center; justify-content:center; width:30px; height:30px; border-radius:10px; background:#f0f5e9; color:#34472f; font-size:1rem; }
.metric-value { font-size:1.85rem; line-height:1.2; font-weight:850; letter-spacing:-.065em; color:#17231e; margin-top:9px; }
.metric-sub { color:#8a948e; font-size:.72rem; margin-top:3px; }
.section-label { font-size:.68rem; letter-spacing:.15em; text-transform:uppercase; font-weight:850; color:#78847c; margin:0 0 5px; }
h1,h2,h3,h4 { letter-spacing:-.04em; }
h3 { font-weight:800; }
[data-testid="stMarkdownContainer"] h4 { font-size:1.13rem; margin-top:.1rem; margin-bottom:.45rem; }
[data-testid="stMarkdownContainer"] p { line-height:1.65; }
div.stButton > button { min-height:2.7rem; border-radius:11px; font-weight:750; border:1px solid #dce2d8; transition:all .16s ease; }
div.stButton > button:hover { border-color:#9ba99c; transform:translateY(-1px); }
div.stButton > button[kind="primary"] { background:var(--sd-lime); color:#17231e; border:1px solid var(--sd-lime); box-shadow:0 3px 0 rgba(23,35,30,.06); }
div.stButton > button[kind="primary"]:hover { background:#d5fb83; border-color:#d5fb83; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input { border-radius:10px; border-color:#dce2d8; background:#fff; }
[data-testid="stCheckbox"] label { font-size:.9rem; }
[data-testid="stDataFrame"] { border:1px solid var(--sd-line); border-radius:13px; overflow:hidden; background:#fff; }
[data-testid="stAlert"] { border-radius:12px; }
[data-testid="stExpander"] { background:#fff; border:1px solid var(--sd-line); border-radius:13px; }
hr { border-color:var(--sd-line); }
@media (max-width: 700px) { [data-testid="stMainBlockContainer"] { padding:1rem .8rem 2rem; } .hero { padding:24px 21px; border-radius:19px; } .hero:after { opacity:.35; right:-150px; } .metric-card { padding:14px; } .metric-value { font-size:1.5rem; } }
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
    st.caption("LOCAL-FIRST PRODUCTIVITY")
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
