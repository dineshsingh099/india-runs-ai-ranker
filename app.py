import json
import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st
from src.pipeline import rank_candidates
from src.jd_parser import parse_job_description

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Redrob India.Runs — AI Candidate Ranker",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Minimal dark styling ─────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
[data-testid="stHeader"] { background: #0d1117; }

h1, h2, h3 { color: #e6edf3; }

.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #3b82f6);
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: 600;
    transition: transform .2s, box-shadow .2s;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(79,70,229,.45);
}

.jd-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 16px;
    line-height: 1.8;
}

.badge {
    background: #1e1b4b;
    color: #818cf8;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.82rem;
    font-weight: 500;
    margin: 3px 4px 3px 0;
    display: inline-block;
    border: 1px solid #312e81;
}

.score-bar-wrap {
    background: #21262d;
    border-radius: 6px;
    height: 8px;
    width: 100%;
    overflow: hidden;
    margin-top: 3px;
}
.score-bar-fill {
    height: 8px;
    border-radius: 6px;
    background: linear-gradient(90deg, #4f46e5, #818cf8);
}

.rank-badge {
    display: inline-block;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    line-height: 32px;
    text-align: center;
    font-weight: 700;
    font-size: 0.9rem;
}

.hp-flag {
    background: #450a0a;
    border: 1px solid #7f1d1d;
    color: #fca5a5;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.80rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🎯 Redrob India.Runs — AI Recruiter Ranking System")
st.markdown(
    "Rank candidates the way a great recruiter would — understanding career history, "
    "skills, behavioral signals, and platform activity. Paste a JD, upload a dataset, run."
)

# ── Default JD ───────────────────────────────────────────────────────────────
DEFAULT_JD = """\
Role: Senior AI Engineer
Location: Pune or Noida, India
Experience: 5+ years

We are looking for a Senior AI Engineer to design and implement production-grade
embeddings-based retrieval and ranking systems at scale. You will own the search
infrastructure, semantic search, vector databases (FAISS, Pinecone, Qdrant), and
hybrid retrieval combining dense and sparse search.

Requirements:
- 5+ years in AI/ML, NLP, and Information Retrieval.
- Proven expertise in Python, PyTorch, LangChain, RAG, and LLM fine-tuning.
- Solid hands-on experience building search systems, dense retrieval, and
  database index optimization.
- Located in or willing to relocate to Pune or Noida.

Preferred:
- Experience with MLOps, vector search engineering, deploying large language models.
"""

# ── Inputs ───────────────────────────────────────────────────────────────────
col_jd, col_up = st.columns([3, 2], gap="large")

with col_jd:
    st.subheader("📝 Job Description")
    jd_text = st.text_area(
        "Paste JD text:",
        value=DEFAULT_JD,
        height=260,
        placeholder="Enter Job Description ...",
        label_visibility="collapsed",
    )

with col_up:
    st.subheader("📂 Candidate Dataset")
    uploaded = st.file_uploader(
        "Upload candidates (.json or .jsonl)",
        type=["json", "jsonl"],
        label_visibility="collapsed",
    )

# ── Load candidates ──────────────────────────────────────────────────────────
candidates = None
if uploaded is not None:
    try:
        content = uploaded.getvalue().decode("utf-8")
        if uploaded.name.endswith(".json"):
            candidates = json.loads(content)
            if isinstance(candidates, dict):
                candidates = [candidates]
        else:
            candidates = [json.loads(l) for l in content.splitlines() if l.strip()]
        st.success(f"Loaded **{len(candidates)}** candidates from `{uploaded.name}`")
    except Exception as exc:
        st.error(f"Failed to load file: {exc}")
else:
    try:
        with open("data/sample_candidates.json", "r", encoding="utf-8") as fh:
            candidates = json.load(fh)
        with col_up:
            st.info(f"Using sample dataset — {len(candidates)} candidates. Upload to override.")
    except FileNotFoundError:
        with col_up:
            st.warning("Upload a candidate dataset to begin.")

# ── JD preview ───────────────────────────────────────────────────────────────
if jd_text.strip():
    parsed = parse_job_description(jd_text)
    st.subheader("🔍 Parsed JD Requirements")
    loc_label  = parsed["location"] or "Any / Remote"
    sen_label  = parsed["seniority"] or "Not specified"
    role_label = parsed["role"] or "—"
    exp_label  = f"{parsed['min_experience']}+ yrs"

    st.markdown(f"""
    <div class="jd-card">
      <b>Role:</b> {role_label} &nbsp;|&nbsp;
      <b>Seniority:</b> {sen_label} &nbsp;|&nbsp;
      <b>Min Exp:</b> {exp_label} &nbsp;|&nbsp;
      <b>Location:</b> {loc_label}
    </div>
    """, unsafe_allow_html=True)

    all_skills = parsed["required_skills"] + parsed["preferred_skills"]
    if all_skills:
        badges = "".join(f'<span class="badge">{s}</span>' for s in all_skills)
        st.markdown(f"**Extracted Skills:** {badges}", unsafe_allow_html=True)

# ── Ranking action ────────────────────────────────────────────────────────────
st.markdown("---")
run_btn = st.button("🚀 Run Recruiter Ranking", type="primary", disabled=(not candidates))

if run_btn and candidates:
    with st.spinner(f"Analysing {len(candidates):,} candidate profiles ..."):
        results = rank_candidates(candidates, jd_text, top_n=len(candidates))

    if not results:
        st.error("Ranking returned no results. Check the candidate dataset format.")
    else:
        st.success(f"Ranked **{len(results):,}** candidates. Top results shown below.")

        # ── Summary table ─────────────────────────────────────────────────
        st.subheader("🏆 Candidate Shortlist")

        table_rows = []
        for r in results:
            hp_flag = " 🚨 Flagged" if r.get("is_honeypot") else ""
            table_rows.append({
                "Rank":        r["rank"],
                "Candidate ID": r["candidate_id"],
                "Score":       f"{r['score']:.4f}",
                "Reasoning":   r["reasoning"],
                "Status":      f"Flagged{hp_flag}" if r.get("is_honeypot") else "Validated",
            })

        df = pd.DataFrame(table_rows)
        st.dataframe(df, width="stretch")

        # ── Per-candidate score breakdown (expanders) ─────────────────────
        st.subheader("📊 Score Breakdown (Top 20)")
        for r in results[:20]:
            sd = r.get("score_details", {})
            label = f"#{r['rank']}  {r['candidate_id']}  —  score {r['score']:.4f}"
            if r.get("is_honeypot"):
                label += "  🚨"
            with st.expander(label):
                c1, c2, c3 = st.columns(3)

                def _bar(col, title, val, note=""):
                    pct = int(round(val * 100))
                    col.markdown(
                        f"**{title}** `{val:.3f}`{(' — ' + note) if note else ''}\n"
                        f'<div class="score-bar-wrap">'
                        f'<div class="score-bar-fill" style="width:{pct}%"></div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                with c1:
                    _bar(c1, "Semantic",   sd.get("semantic_score", 0))
                    _bar(c1, "Skill",      sd.get("skill_score", 0))
                with c2:
                    _bar(c2, "Title",      sd.get("title_score", 0))
                    _bar(c2, "Experience", sd.get("exp_score", 0))
                with c3:
                    _bar(c3, "Behavioral", sd.get("behavioral_score", 0))
                    _bar(c3, "Location",   sd.get("loc_score", 0))

                # Matched skills
                matched = sd.get("matched_core", [])
                if matched:
                    badges = "".join(f'<span class="badge">{s}</span>' for s in matched)
                    st.markdown(f"**Matched skills:** {badges}", unsafe_allow_html=True)

                # Penalty info
                pens = sd.get("penalty_reasons", [])
                if pens:
                    st.warning("  |  ".join(pens))

                # Honeypot reasons
                if r.get("is_honeypot"):
                    hp_r = sd.get("honeypot_reasons", [])
                    st.error("**FLAGGED — " + (hp_r[0] if hp_r else "profile inconsistency") + "**")

                st.caption(r.get("reasoning", ""))

        # ── CSV download ──────────────────────────────────────────────────
        csv_df = pd.DataFrame([
            {
                "candidate_id": r["candidate_id"],
                "rank":         r["rank"],
                "score":        r["score"],
                "reasoning":    r["reasoning"],
            }
            for r in results[:100]
        ])
        csv_bytes = csv_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download submission.csv (top 100)",
            csv_bytes,
            file_name="submission.csv",
            mime="text/csv",
        )