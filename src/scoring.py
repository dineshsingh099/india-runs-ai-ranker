import config as cfg
from src import features as feat
from src.honeypot import honeypot_score


def score_candidate(cand, semantic_score):
    title_score, title_current_w = feat.title_tier_score(cand)
    skill_score, matched_core = feat.skill_match_score(cand)
    exp_score = feat.experience_fit_score(cand)
    loc_score = feat.location_fit_score(cand)
    notice_score = feat.notice_period_score(cand)
    mod = feat.behavioral_modifier(cand)
    penalty, penalty_reasons = feat.disqualifier_penalties(cand, "")
    is_hp, n_flags, hp_reasons = honeypot_score(cand)

    base = (
        cfg.W_TITLE * title_score
        + cfg.W_SKILL * skill_score
        + cfg.W_SEMANTIC * semantic_score
        + cfg.W_EXPERIENCE * exp_score
        + cfg.W_LOCATION * loc_score
        + cfg.W_NOTICE * notice_score
    )
    base = base * mod + penalty

    if is_hp:
        base = min(base, 0.03)  # force honeypots to the very bottom, never top-100

    final = max(0.0, min(1.0, base))

    return {
        "score": final,
        "title_score": title_score,
        "title_current_w": title_current_w,
        "skill_score": skill_score,
        "matched_core": matched_core,
        "exp_score": exp_score,
        "loc_score": loc_score,
        "notice_score": notice_score,
        "behavioral_mod": mod,
        "penalty": penalty,
        "penalty_reasons": penalty_reasons,
        "is_honeypot": is_hp,
        "honeypot_flags": n_flags,
        "honeypot_reasons": hp_reasons,
        "semantic_score": semantic_score,
    }
