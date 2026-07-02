"""
Honeypot detection via internal profile inconsistency.

submission_spec.md warns: "~80 honeypot candidates with subtly impossible
profiles (e.g., 8 years of experience at a company founded 3 years ago;
'expert' proficiency in 10 skills with 0 years used)". Company founding
dates are not part of the released schema, so we detect the class of
inconsistency that *is* computable from the given fields:

  1. 'Expert' (or 'advanced') proficiency claimed with ~0 months of
     actual use of that skill, across many skills at once.
  2. Sum of career_history duration_months substantially exceeds what
     years_of_experience allows (double-counted / overlapping / invented
     tenure).
  3. Career history date arithmetic that doesn't add up (end before
     start, is_current=True with a non-null end_date, negative gaps).
  4. redrob_signals values that violate their own documented bounds
     (e.g. rates > 1.0, negative counts) -- a value that is only reachable
     if the profile was hand-crafted to be "impossible" rather than
     sampled from the documented generator.
  5. Education end_year before start_year.

A candidate is flagged as a honeypot if it trips >=2 independent checks
(single-check trips are common noise in a large synthetic pool and are not
penalized as hard).
"""
from datetime import date


def _parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def honeypot_score(cand):
    """Return (is_honeypot: bool, weight: float, reasons: list[str]).

    Checks are weighted: a single severely-impossible signal (e.g. career
    history that totals nearly 3 years more than the claimed total
    experience) is treated as seriously as two mild ones, matching the
    spec's framing of honeypots as "subtly impossible" -- often just one
    but glaring inconsistency.
    """
    flags = []
    weight = 0.0

    # 1. expert/advanced skill claimed with ~0 duration
    skills = cand.get("skills") or []
    zero_duration_expert = sum(
        1 for s in skills
        if s.get("proficiency") in ("expert", "advanced") and s.get("duration_months", 0) == 0
    )
    if zero_duration_expert >= 3:
        flags.append(f"{zero_duration_expert} expert/advanced skills with 0 months used")
        weight += 2.0
    elif zero_duration_expert >= 1:
        weight += 0.5

    # 2. career history months vs years_of_experience
    yoe = cand.get("profile", {}).get("years_of_experience", 0) or 0
    total_months = sum(ch.get("duration_months", 0) for ch in cand.get("career_history", []))
    overshoot = total_months - (yoe * 12)
    if overshoot > 30:
        flags.append(f"career_history totals {total_months}mo but years_of_experience={yoe}")
        weight += 2.0
    elif overshoot > 18:
        flags.append(f"career_history totals {total_months}mo but years_of_experience={yoe}")
        weight += 1.0

    # 3. date arithmetic
    for ch in cand.get("career_history", []):
        sd, ed = _parse_date(ch.get("start_date")), _parse_date(ch.get("end_date"))
        if ch.get("is_current") and ch.get("end_date") not in (None, ""):
            flags.append("is_current=True but end_date is set")
            weight += 1.5
        if sd and ed and ed < sd:
            flags.append("career_history end_date before start_date")
            weight += 1.5

    # 4. redrob_signals out-of-bound values
    rs = cand.get("redrob_signals", {}) or {}
    if rs.get("recruiter_response_rate", 0) is not None and rs.get("recruiter_response_rate", 0) > 1.0:
        flags.append("recruiter_response_rate > 1.0")
        weight += 2.0
    if rs.get("interview_completion_rate", 0) is not None and rs.get("interview_completion_rate", 0) > 1.0:
        flags.append("interview_completion_rate > 1.0")
        weight += 2.0
    oar = rs.get("offer_acceptance_rate", 0)
    if oar is not None and not (-1.0 <= oar <= 1.0):
        flags.append("offer_acceptance_rate out of [-1,1]")
        weight += 2.0
    if rs.get("notice_period_days", 0) is not None and rs.get("notice_period_days", 0) > 180:
        flags.append("notice_period_days > documented max of 180")
        weight += 2.0

    # 5. education year arithmetic
    for ed_entry in cand.get("education", []):
        sy, ey = ed_entry.get("start_year"), ed_entry.get("end_year")
        if sy and ey and ey < sy:
            flags.append("education end_year before start_year")
            weight += 1.0

    is_honeypot = weight >= 2.0
    return is_honeypot, weight, flags
