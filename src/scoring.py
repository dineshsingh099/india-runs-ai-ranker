from src.skills import compute_skill_score
from src.title_match import compute_title_score
from src.experience import compute_experience_score
from src.behavioral import compute_behavioral_score
from src.location import compute_location_score
from src.honeypot import honeypot_score
from src.progression import compute_progression_score
from src.domain import compute_domain_score

# Hybrid scoring weights (sum = 1.0)
W_SEMANTIC    = 0.20
W_SKILL       = 0.20
W_TITLE       = 0.15
W_EXPERIENCE  = 0.08
W_BEHAVIORAL  = 0.20
W_PROGRESSION = 0.07
W_DOMAIN      = 0.05
W_LOCATION    = 0.025
W_NOTICE      = 0.025

# Education tier bonus constants
_EDU_TIER_BONUS = {"tier_1": 0.04, "tier_2": 0.02, "tier_3": 0.01}


def _notice_period_score(candidate):
    rs = candidate.get("redrob_signals", {}) or {}
    days = rs.get("notice_period_days")
    if days is None:
        return 0.5
    if days <= 15:
        return 1.0
    if days <= 30:
        return 0.90
    if days <= 60:
        return 0.70
    if days <= 90:
        return 0.45
    return 0.20


def _job_hopper_penalty(candidate):
    history = candidate.get("career_history", []) or []
    tenures = [ch.get("duration_months", 0) or 0 for ch in history]
    if len(tenures) >= 3:
        avg = sum(tenures) / len(tenures)
        if avg < 12:
            return 0.15, "very short average tenure (%.0f mo) — serial job-hopper pattern" % avg
        if avg < 18:
            return 0.08, "short average tenure (%.0f mo) — possible title-chasing pattern" % avg
    return 0.0, ""


def _education_bonus(candidate):
    """Small bonus for top-tier academic institutions (generalises across roles)."""
    best = 0.0
    for edu in candidate.get("education", []) or []:
        tier = edu.get("tier", "")
        best = max(best, _EDU_TIER_BONUS.get(tier, 0.0))
    return best


def score_candidate(cand, semantic_score, jd_criteria):
    """
    Scores a single candidate against parsed JD criteria.

    Args:
        cand           – candidate dict
        semantic_score – Cosine sim in [0, 1] (dense or tf-idf)
        jd_criteria    – output of parse_job_description() + domain_weights

    Returns dict with 'score' + all component breakdowns.
    """
    skill_score, matched_core, stuffing_pen = compute_skill_score(
        cand,
        jd_criteria.get("required_skills", []),
        jd_criteria.get("preferred_skills", []),
    )
    title_score, current_title_sim = compute_title_score(cand, jd_criteria.get("role", ""))
    exp_score   = compute_experience_score(cand, jd_criteria.get("min_experience", 0))
    beh_score   = compute_behavioral_score(cand)
    loc_score   = compute_location_score(cand, jd_criteria.get("location", ""))
    notice_score = _notice_period_score(cand)
    edu_bonus   = _education_bonus(cand)
    
    # Career progression score
    prog_score  = compute_progression_score(cand)
    
    # Domain relevance score
    jd_domain_weights = jd_criteria.get("domain_weights", {"ML": 1.0})
    dom_score   = compute_domain_score(cand, jd_domain_weights)

    # ── Honeypot check ────────────────────────────────────────────────
    is_hp, hp_weight, hp_reasons = honeypot_score(cand)

    # ── Penalty accumulation ─────────────────────────────────────────
    penalty_reasons = []
    total_penalty   = 0.0

    hop_pen, hop_reason = _job_hopper_penalty(cand)
    if hop_pen > 0:
        total_penalty += hop_pen
        penalty_reasons.append(hop_reason)

    if stuffing_pen > 0:
        total_penalty += stuffing_pen
        penalty_reasons.append("many low-relevance skills listed — possible keyword stuffing")

    # Non-technical title applying for a clearly technical role
    if current_title_sim == 0.0 and title_score == 0.0:
        total_penalty += 0.25
        penalty_reasons.append("career background not aligned with the target technical role")

    # ── Hybrid weighted sum ───────────────────────────────────────────
    weighted_sum = (
        W_SEMANTIC     * semantic_score
        + W_SKILL      * skill_score
        + W_TITLE      * title_score
        + W_EXPERIENCE * exp_score
        + W_BEHAVIORAL * beh_score
        + W_PROGRESSION * prog_score
        + W_DOMAIN     * dom_score
        + W_LOCATION   * loc_score
        + W_NOTICE     * notice_score
        + edu_bonus
    )

    final_score = weighted_sum - total_penalty

    if is_hp:
        final_score = min(final_score, 0.03)

    final_score = max(0.0, min(1.0, final_score))

    return {
        "score":            final_score,
        "semantic_score":   semantic_score,
        "skill_score":      skill_score,
        "title_score":      title_score,
        "exp_score":        exp_score,
        "behavioral_score": beh_score,
        "progression_score": prog_score,
        "domain_score":     dom_score,
        "loc_score":        loc_score,
        "notice_score":     notice_score,
        "edu_bonus":        edu_bonus,
        "matched_core":     matched_core,
        "penalty":          total_penalty,
        "penalty_reasons":  penalty_reasons,
        "is_honeypot":      is_hp,
        "honeypot_reasons": hp_reasons,
        "title_current_w":  current_title_sim,
    }
