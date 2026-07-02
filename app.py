import json
import pandas as pd
import streamlit as st
from src.pipeline import rank_candidates

st.set_page_config(
    page_title="Redrob India.Runs — Candidate Ranker",
    layout="wide"
)

st.title("Redrob India.Runs — Candidate Ranking Sandbox")

st.caption(
    "Hybrid ranker: title-tier gating + skill credibility scoring + "
    "TF-IDF semantic fit + behavioral-signal modifier + honeypot filtering. "
    "Runs fully on CPU without network access."
)

with st.expander("How to use"):
    st.markdown(
        "- Upload a `.json` file containing candidate records.\n"
        "- Or use the bundled sample dataset.\n"
        "- Click **Run Ranking** to generate rankings and download the CSV."
    )

uploaded = st.file_uploader(
    "Upload candidate sample (.json, max 100 candidates)",
    type=["json"]
)

candidates = None

if uploaded is not None:
    candidates = json.load(uploaded)

    if isinstance(candidates, dict):
        candidates = [candidates]

    st.success(f"Loaded {len(candidates)} candidates from upload.")

else:
    try:
        with open("data/sample_candidates.json", "r", encoding="utf-8") as f:
            candidates = json.load(f)

        st.info(
            f"Using bundled sample dataset ({len(candidates)} candidates)."
        )

    except FileNotFoundError:
        st.warning("Please upload a candidate JSON file.")

if candidates:

    if len(candidates) > 100:
        st.warning(
            f"Only the first 100 candidates will be processed "
            f"out of {len(candidates)}."
        )
        candidates = candidates[:100]

    if st.button("Run Ranking", type="primary"):

        with st.spinner("Ranking candidates..."):
            results = rank_candidates(
                candidates,
                top_n=len(candidates)
            )

        df = pd.DataFrame([
            {
                "rank": r["rank"],
                "candidate_id": r["candidate_id"],
                "score": r["score"],
                "reasoning": r["reasoning"],
                "honeypot_flag": r["is_honeypot"]
            }
            for r in results
        ])

        st.dataframe(
            df,
            width="stretch",
            hide_index=True
        )

        with st.expander("Top 10 Score Breakdown"):

            for r in results[:10]:
                d = r["detail"]

                st.markdown(
                    f"**#{r['rank']} {r['candidate_id']}** — "
                    f"score {r['score']}  \n"
                    f"title={d['title_score']:.2f} · "
                    f"skill={d['skill_score']:.2f} · "
                    f"semantic={d['semantic_score']:.2f} · "
                    f"experience={d['exp_score']:.2f} · "
                    f"location={d['loc_score']:.2f} · "
                    f"notice={d['notice_score']:.2f} · "
                    f"behavioral_x{d['behavioral_mod']:.2f} · "
                    f"penalty={d['penalty']:.2f}"
                )

        csv_bytes = (
            df[
                ["candidate_id", "rank", "score", "reasoning"]
            ]
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "Download Ranked CSV",
            csv_bytes,
            file_name="submission_sample.csv",
            mime="text/csv"
        )