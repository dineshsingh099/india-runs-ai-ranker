from datetime import date

_REF_DATE = date(2026, 7, 2)


def _days_since(date_str):
    if not date_str:
        return None
    try:
        return (_REF_DATE - date.fromisoformat(str(date_str)[:10])).days
    except Exception:
        return None


def compute_behavioral_score(candidate):
    """
    Normalised behavioral engagement + availability score in [0, 1].
    Uses ALL redrob_signals fields. Missing fields contribute 0 (neutral).
    Base = 0.50.
    """
    rs = candidate.get("redrob_signals", {}) or {}
    if not rs:
        return 0.5

    score = 0.50

    # 1. Open to work — strongest intent signal
    otw = rs.get("open_to_work_flag")
    if otw is True:
        score += 0.14
    elif otw is False:
        score -= 0.08

    # 2. Recruiter response rate
    rrr = rs.get("recruiter_response_rate")
    if rrr is not None and 0 <= rrr <= 1:
        score += (rrr - 0.5) * 0.20

    # 3. Average response time (hours) — lower = better
    art = rs.get("avg_response_time_hours")
    if art is not None and art >= 0:
        score += max(-0.05, min(0.05, (24.0 - art) / 24.0 * 0.05))

    # 4. Activity recency
    days_inactive = _days_since(rs.get("last_active_date"))
    if days_inactive is not None:
        if days_inactive <= 7:
            score += 0.10
        elif days_inactive <= 30:
            score += 0.06
        elif days_inactive <= 90:
            score += 0.02
        elif days_inactive <= 180:
            score -= 0.06
        else:
            score -= 0.12

    # 5. Profile completeness (baseline 70 %)
    completeness = rs.get("profile_completeness_score")
    if completeness is not None and 0 <= completeness <= 100:
        score += (completeness - 70.0) / 100.0 * 0.08

    # 6. Interview completion rate
    icr = rs.get("interview_completion_rate")
    if icr is not None and 0 <= icr <= 1:
        score += (icr - 0.70) * 0.10

    # 7. Offer acceptance rate (-1 = no history → neutral)
    oar = rs.get("offer_acceptance_rate")
    if oar is not None and oar != -1 and -1 <= oar <= 1:
        score += oar * 0.04

    # 8. GitHub activity
    gh = rs.get("github_activity_score")
    if gh is not None and gh >= 0:
        score += min(0.07, gh / 100.0 * 0.07)

    # 9. Platform skill assessments
    assessments = rs.get("skill_assessment_scores") or {}
    if assessments:
        avg_a = sum(assessments.values()) / len(assessments)
        score += min(0.06, avg_a / 100.0 * 0.06)

    # 10. Connection count
    conn = rs.get("connection_count") or 0
    if conn >= 500:
        score += 0.04
    elif conn >= 200:
        score += 0.02

    # 11. Endorsements received
    ends = rs.get("endorsements_received") or 0
    score += min(0.03, ends / 200.0 * 0.03)

    # 12. Recruiter visibility
    sa = rs.get("search_appearance_30d") or 0
    sv = rs.get("saved_by_recruiters_30d") or 0
    score += min(0.04, (sa + sv * 2) / 300.0 * 0.04)

    # 13. Active job-seeking (applications submitted)
    apps = rs.get("applications_submitted_30d") or 0
    if apps >= 3:
        score += 0.02

    # 14. Verified identity + LinkedIn
    if rs.get("verified_email") and rs.get("verified_phone"):
        score += 0.02
    if rs.get("linkedin_connected"):
        score += 0.01

    return max(0.0, min(1.0, score))
