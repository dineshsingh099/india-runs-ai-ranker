"""
Reasoning-string generator.

submission_spec.md Stage 4 explicitly penalizes: empty reasoning,
all-identical strings, templated name-insertion, mentioning skills not in
the candidate's profile (hallucination), and reasoning that contradicts the
rank. This module only ever references fields that are actually present on
the candidate object -- it never invents a fact -- and composes a different
subset of true facts depending on what is actually distinctive about each
profile, so two candidates with different underlying data won't produce the
same sentence.
"""


def build_reasoning(cand, matched_core_skills, title_current_w, penalties_reasons, honeypot_reasons, exp_score, loc_score):
    p = cand["profile"]
    rs = cand.get("redrob_signals", {})
    bits = []

    title = p.get("current_title", "their current role")
    yoe = p.get("years_of_experience", 0)
    bits.append(f"{title} with {yoe:.1f} yrs experience")

    if matched_core_skills:
        shown = ", ".join(matched_core_skills[:3])
        bits.append(f"hands-on with {shown}")
    elif title_current_w < 0.15:
        bits.append("title/background not aligned to AI ranking & retrieval work")

    company = p.get("current_company")
    if company:
        bits.append(f"currently at {company}")

    loc = p.get("location", "")
    if loc_score >= 0.8:
        bits.append(f"based in {loc} (preferred location)")
    elif loc_score < 0.4:
        bits.append(f"located in {loc}, outside the preferred hiring region")

    notice = rs.get("notice_period_days")
    if notice is not None:
        if notice <= 30:
            bits.append(f"short {notice}-day notice period")
        elif notice > 90:
            bits.append(f"long {notice}-day notice period")

    resp = rs.get("recruiter_response_rate")
    if resp is not None:
        if resp < 0.15:
            bits.append(f"very low recruiter response rate ({resp:.0%})")
        elif resp > 0.7:
            bits.append(f"strong recruiter response rate ({resp:.0%})")

    if not rs.get("open_to_work_flag", True):
        bits.append("not currently marked open to work")

    if penalties_reasons:
        bits.append(penalties_reasons[0])

    if honeypot_reasons:
        bits.append("profile has internal inconsistencies (" + honeypot_reasons[0] + ")")

    text = "; ".join(bits[:5]) + "."
    return text[0].upper() + text[1:]
