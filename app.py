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
:root { --sloth-ink:#17211d; --sloth-muted:#6c7972; --sloth-green:#b8f36b; --sloth-paper:#f6f7f2; }
html, body, [class*="css"] { font-family: 'Segoe UI', Arial, sans-serif; }
.stApp { background: var(--sloth-paper); color: var(--sloth-ink); }
[data-testid="stSidebar"] { background: #202b26; }
[data-testid="stSidebar"] * { color: #f4f7f1; }
.hero { background: #202b26; border-radius: 24px; padding: 32px 36px; color: #f5f7f2; margin-bottom: 20px; }
.hero h1 { color: #f5f7f2; font-size: clamp(2rem,4vw,3.2rem); line-height: 1.05; letter-spacing: -0.06em; margin: 0; }
.hero p { color: #c7d1c9; font-size: 1rem; max-width: 700px; margin: 12px 0 0; }
.hero .tag { display:inline-block; background:var(--sloth-green); color:#17211d; border-radius:999px; padding:5px 10px; font-size:.75rem; font-weight:800; margin-bottom:18px; }
.metric-card { background:white; border:1px solid #e4e9e1; border-radius:16px; padding:18px 20px; min-height:100px; }
.metric-label { color:#6c7972; font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
.metric-value { font-size:1.8rem; font-weight:800; letter-spacing:-.05em; color:#202b26; margin-top:5px; }
.section-label { font-size:.75rem; letter-spacing:.12em; text-transform:uppercase; font-weight:800; color:#6c7972; }
div.stButton > button[kind="primary"] { background:#b8f36b; color:#17211d; border:0; border-radius:10px; font-weight:800; }
div.stButton > button { border-radius:10px; }
div[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; }
.small-note { color:#6c7972; font-size:.86rem; }
</style>
""", unsafe_allow_html=True)

if "files" not in st.session_state:
    st.session_state.files = []
if "plan" not in st.session_state:
    st.session_state.plan = []
if "last_results" not in st.session_state:
    st.session_state.last_results = []

with st.sidebar:
    st.markdown("## 🦥 SlothDesk")
    st.caption("Local-first productivity assistant")
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
  <span class="tag">LESS BUSYWORK. MORE HEADSPACE.</span>
  <h1>Let your files<br>sort themselves out.</h1>
  <p>A calm, local-first workspace that finds the clutter, suggests a better home for your files, and waits for your approval before changing anything.</p>
</div>
""", unsafe_allow_html=True)

top1, top2, top3 = st.columns(3)
with top1:
    st.markdown('<div class="metric-card"><div class="metric-label">Files scanned</div><div class="metric-value">' + str(len(st.session_state.files)) + '</div></div>', unsafe_allow_html=True)
with top2:
    total_bytes = sum(int(item.get("size_bytes", 0)) for item in st.session_state.files)
    st.markdown('<div class="metric-card"><div class="metric-label">Space reviewed</div><div class="metric-value">' + (f"{total_bytes / (1024 * 1024):.1f} MB" if total_bytes < 1024**3 else f"{total_bytes / (1024**3):.2f} GB") + '</div></div>', unsafe_allow_html=True)
with top3:
    pending = len(st.session_state.plan)
    st.markdown('<div class="metric-card"><div class="metric-label">Suggested actions</div><div class="metric-value">' + str(pending) + '</div></div>', unsafe_allow_html=True)

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
