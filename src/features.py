"""Structured (non-text) feature extraction for a single candidate dict."""
import math
from datetime import date

import config as cfg


def title_tier_score(cand):
    """0.7 * tier(current title) + 0.3 * best tier among past titles.

    Rewards a candidate whose *current* title is the strongest evidence, but
    still gives partial credit to someone who has ML-relevant history and
    has recently moved to an adjacent role (or vice versa) -- the JD
    explicitly says title alone shouldn't be a hard gate, only a strong
    prior.
    """
    current = cand["profile"]["current_title"]
    current_w = cfg.TITLE_TIER.get(current, cfg.DEFAULT_TITLE_WEIGHT)

    past_titles = [ch.get("title") for ch in cand.get("career_history", [])]
    past_w = max([cfg.TITLE_TIER.get(t, cfg.DEFAULT_TITLE_WEIGHT) for t in past_titles], default=0.0)

    return 0.7 * current_w + 0.3 * past_w, current_w


def skill_match_score(cand):
    """Sum of (category_weight * proficiency_trust) across candidate skills,
    normalized to [0,1]. proficiency_trust requires actual duration_months,
    which is what defeats the keyword-stuffing trap: listing 'Pinecone' as
    'expert' with duration_months=0 earns almost nothing.
    """
    raw = 0.0
    matched = []
    for s in cand.get("skills", []):
        w = cfg.SKILL_WEIGHTS.get(s.get("name"), 0.0)
        if w <= 0:
            continue
        prof_mult = cfg.PROFICIENCY_MULT.get(s.get("proficiency"), 0.4)
        duration_trust = min(1.0, (s.get("duration_months", 0) or 0) / 12.0)
        # a skill with 0 months' use gets at most 15% credit regardless of claimed proficiency
        duration_trust = max(duration_trust, 0.15) if (s.get("duration_months", 0) or 0) > 0 else 0.15
        endorsement_bonus = min(1.15, 1.0 + 0.01 * min(s.get("endorsements", 0) or 0, 15))
        contrib = w * prof_mult * duration_trust * endorsement_bonus
        raw += contrib
        if w >= 2.0 and contrib > 0.3:
            matched.append(s["name"])
    norm = min(1.0, raw / cfg.MAX_SKILL_RAW_SCORE)
    return norm, matched


def experience_fit_score(cand):
    """Peaks at 5-9 yrs (JD's stated band), tapers smoothly outside it --
    the JD explicitly says the band is 'a range, not a requirement'."""
    yoe = cand["profile"].get("years_of_experience", 0) or 0
    if 5 <= yoe <= 9:
        return 1.0
    if yoe < 5:
        gap = 5 - yoe
        return max(0.0, 1.0 - 0.18 * gap)
    gap = yoe - 9
    return max(0.0, 1.0 - 0.10 * gap)


def location_fit_score(cand):
    loc = cand["profile"].get("location", "")
    country = cand["profile"].get("country", "")
    city = loc.split(",")[0].strip()
    if country != "India":
        base = cfg.NON_INDIA_PENALTY_BASE
    elif city in cfg.PRIMARY_LOCATIONS:
        base = 1.0
    elif city in cfg.TIER1_INDIA_CITIES:
        base = 0.80
    else:
        base = cfg.OTHER_INDIA_CITIES_PENALTY

    willing = cand.get("redrob_signals", {}).get("willing_to_relocate", False)
    if base < 1.0 and willing:
        base = min(1.0, base + 0.20)
    return base


def notice_period_score(cand):
    days = cand.get("redrob_signals", {}).get("notice_period_days", 60) or 0
    if days <= 30:
        return 1.0
    if days <= 60:
        return 0.7
    if days <= 90:
        return 0.45
    return 0.25


def behavioral_modifier(cand):
    """Multiplicative modifier in ~[0.72, 1.15]. Captures the JD's explicit
    instruction: 'a perfect-on-paper candidate who hasn't logged in for 6
    months and has a 5% recruiter response rate is, for hiring purposes,
    not actually available. Down-weight them appropriately.'
    """
    rs = cand.get("redrob_signals", {})
    mod = 1.0

    if not rs.get("open_to_work_flag", False):
        mod -= 0.10

    last_active = rs.get("last_active_date")
    if last_active:
        try:
            days_inactive = (date(2026, 7, 2) - date.fromisoformat(last_active[:10])).days
        except ValueError:
            days_inactive = 0
        if days_inactive > 180:
            mod -= 0.15
        elif days_inactive > 90:
            mod -= 0.08
        elif days_inactive <= 14:
            mod += 0.04

    resp = rs.get("recruiter_response_rate", 0.5) or 0.0
    mod += (resp - 0.5) * 0.20  # +/-0.10 swing

    interview_rate = rs.get("interview_completion_rate", 0.7) or 0.0
    mod += (interview_rate - 0.7) * 0.08

    oar = rs.get("offer_acceptance_rate", -1)
    if oar is not None and oar >= 0:
        mod += (oar - 0.5) * 0.06

    if rs.get("verified_email") and rs.get("verified_phone"):
        mod += 0.02

    gh = rs.get("github_activity_score", -1)
    if gh is not None and gh >= 0:
        mod += min(0.05, gh / 100.0 * 0.05)

    completeness = rs.get("profile_completeness_score", 70) or 0
    mod += (completeness - 70) / 100.0 * 0.06

    return max(0.72, min(1.15, mod))


def disqualifier_penalties(cand, career_text):
    """Additive (negative) penalties for the JD's explicit 'do NOT want' list
    that are directly computable from structured fields (text-based versions
    of the same disqualifiers are additionally captured by the semantic
    negative-anchor score in text_similarity.py -- this is a belt-and-braces
    structured check, not a duplicate of it).
    """
    penalty = 0.0
    reasons = []

    # Consulting-only career (explicit named firms), no product company at all
    companies = {ch.get("company") for ch in cand.get("career_history", [])}
    companies.add(cand["profile"].get("current_company"))
    non_consulting = companies - cfg.CONSULTING_FIRMS
    if companies and not non_consulting:
        penalty -= 0.35
        reasons.append("career entirely at consulting firms (TCS/Infosys/Wipro/Accenture/Cognizant/Capgemini), no product-company experience")

    # Job-hopper / title-chaser: short average tenure with escalating seniority titles
    tenures = [ch.get("duration_months", 0) for ch in cand.get("career_history", [])]
    if len(tenures) >= 3:
        avg_tenure = sum(tenures) / len(tenures)
        if avg_tenure < 15:
            penalty -= 0.12
            reasons.append("short average job tenure (~%.0f months), title-chasing pattern" % avg_tenure)

    # Pure CV/Speech without any NLP/retrieval signal
    skill_names = {s.get("name") for s in cand.get("skills", [])}
    cv_speech = {"CNN", "Computer Vision", "Image Classification", "Object Detection",
                 "YOLO", "OpenCV", "GANs", "Diffusion Models", "ASR", "TTS", "Speech Recognition"}
    nlp_retrieval = {"NLP", "Natural Language Processing", "Embeddings", "Semantic Search",
                      "Vector Search", "Information Retrieval", "RAG", "LLMs", "Sentence Transformers"}
    if len(skill_names & cv_speech) >= 3 and len(skill_names & nlp_retrieval) == 0:
        penalty -= 0.18
        reasons.append("primary expertise is computer vision/speech with no NLP or retrieval exposure")

    return penalty, reasons
