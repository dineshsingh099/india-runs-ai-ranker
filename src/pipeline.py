from src.jd_parser import parse_job_description
from src.semantic import compute_semantic_scores
from src.scoring import score_candidate
from src.reasoning import build_reasoning
from src.domain import extract_jd_domain_weights

def rank_candidates(candidates, jd_text, top_n=100):
    """
    Ranks candidates against a Job Description using a 2-stage pipeline:
    Stage 1: Fast Screening using lightweight features & TF-IDF semantic match (all candidates).
    Stage 2: High-fidelity Dense semantic matching (SentenceTransformers) on top 3,000 candidates.
    
    Args:
        candidates (list[dict]): list of candidate profile dicts
        jd_text (str): raw pasted job description text
        top_n (int): number of top candidates to return (defaults to 100)
        
    Returns:
        list[dict]: sorted and ranked candidate entries ready for display or CSV output
    """
    if not candidates:
        return []
        
    # Extract candidate skills vocab dynamically for zero-overfitting
    candidate_skills_vocab = set()
    for cand in candidates:
        for s in cand.get("skills", []) or []:
            s_name = s.get("name")
            if s_name:
                candidate_skills_vocab.add(s_name.lower().strip())

    # 1. Parse Job Description & Extract Domain Weights
    jd_criteria = parse_job_description(jd_text, candidate_skills_vocab)
    jd_criteria["domain_weights"] = extract_jd_domain_weights(jd_text)
    
    # 2. Stage 1: Fast Screening (TF-IDF Semantic Match for all candidates)
    # This takes ~10-15s for 100,000 candidates and narrows the pool down.
    stage1_semantic_scores = compute_semantic_scores(candidates, jd_text, use_dense=False)
    
    screened = []
    for idx, (cand, sem) in enumerate(zip(candidates, stage1_semantic_scores)):
        # Compute first stage screening score
        res = score_candidate(cand, float(sem), jd_criteria)
        screened.append({
            "index": idx,
            "score": res["score"],
            "res": res
        })
        
    # Sort all candidates by Stage 1 score descending
    screened.sort(key=lambda x: -x["score"])
    
    # Slice to top 3,000 for Stage 2 dense re-ranking
    k = min(len(candidates), 3000)
    top_screened = screened[:k]
    
    # 3. Stage 2: Dense Semantic Re-Ranking using SentenceTransformers
    # Runs in 10-15s on CPU for 3,000 candidates instead of minutes for 100,000.
    top_candidates_list = [candidates[item["index"]] for item in top_screened]
    stage2_semantic_scores = compute_semantic_scores(top_candidates_list, jd_text, use_dense=True)
    
    # Re-score the top 3,000 candidates using dense semantic similarity
    re_scored = []
    for item, dense_sem in zip(top_screened, stage2_semantic_scores):
        cand = candidates[item["index"]]
        res = score_candidate(cand, float(dense_sem), jd_criteria)
        rounded_score = round(res["score"], 4)
        re_scored.append({
            "candidate_id": cand.get("candidate_id", ""),
            "score": rounded_score,
            "is_honeypot": res["is_honeypot"],
            "score_details": res,
            "candidate_obj": cand
        })
        
    # 4. Final deterministic sorting: score (descending) and candidate_id (ascending)
    re_scored.sort(key=lambda r: (-r["score"], r["candidate_id"]))
    
    # Slice to top_n
    top_candidates = re_scored[:top_n]

    # 5. Generate recruiter-style reasoning justifications and ranks for top_n
    results = []
    for rank, item in enumerate(top_candidates, start=1):
        reasoning = build_reasoning(item["candidate_obj"], item["score_details"])
        results.append({
            "rank":         rank,
            "candidate_id": item["candidate_id"],
            "score":        item["score"],
            "reasoning":    reasoning,
            "is_honeypot":  item["is_honeypot"],
            "score_details": item["score_details"],
        })
        
    return results
