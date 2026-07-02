import config as cfg
from src.text_similarity import build_candidate_text, compute_semantic_scores
from src.scoring import score_candidate
from src.reasoning import build_reasoning


def rank_candidates(candidates, top_n=None):
    """candidates: list[dict] (parsed candidate JSON objects).
    Returns a list of row dicts, best fit first, length == min(top_n, len(candidates)).
    """
    top_n = top_n or cfg.TOP_N
    texts = [build_candidate_text(c) for c in candidates]
    semantic_scores = compute_semantic_scores(texts)

    results = []
    for cand, sem in zip(candidates, semantic_scores):
        s = score_candidate(cand, float(sem))
        results.append((cand, s))

    results.sort(key=lambda cs: (-cs[1]["score"], cs[0]["candidate_id"]))
    top = results[:top_n]

    prelim = []
    for cand, s in top:
        reasoning = build_reasoning(
            cand, s["matched_core"], s["title_current_w"],
            s["penalty_reasons"], s["honeypot_reasons"], s["exp_score"], s["loc_score"],
        )
        prelim.append({"candidate_id": cand["candidate_id"], "score": round(s["score"], 4),
                        "reasoning": reasoning, "is_honeypot": s["is_honeypot"], "detail": s})

    prelim.sort(key=lambda r: (-r["score"], r["candidate_id"]))
    for i in range(1, len(prelim)):
        if prelim[i]["score"] > prelim[i - 1]["score"]:
            prelim[i]["score"] = prelim[i - 1]["score"]

    for rank, row in enumerate(prelim, start=1):
        row["rank"] = rank

    return prelim
