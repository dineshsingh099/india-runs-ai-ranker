def build_reasoning(cand, score_details):
    """
    Generates a natural, recruiter-style 2-sentence explanation.
    Factual and customized to avoid repeating identical templates.
    """
    profile = cand.get("profile", {}) or {}
    rs      = cand.get("redrob_signals", {}) or {}
    
    title = profile.get("current_title", "")
    yoe   = profile.get("years_of_experience")
    if yoe is None or yoe < 0:
        total_mo = sum((ch.get("duration_months") or 0) for ch in (cand.get("career_history", []) or []))
        yoe = round(total_mo / 12.0, 1) if total_mo > 0 else 0.0
        
    matched = score_details.get("matched_core", [])
    skills_str = ", ".join(matched[:3]) if matched else ""
    
    # ── HONEYPOT FLAG ──────────────────────────────────────────────────
    if score_details.get("is_honeypot"):
        hp_r = score_details.get("honeypot_reasons", [])
        reason = hp_r[0] if hp_r else "profile inconsistencies"
        return f"Flagged candidate due to critical inconsistency: {reason}. This profile shows impossible metrics and has been relegated."

    # ── Sentence 1: Title, YOE, Skills, and Domain ─────────────────────
    s1_templates = [
        "A {title} with {yoe:.1f} years of experience, showing strong hands-on expertise in {skills}.",
        "With {yoe:.1f} years of experience as a {title}, they exhibit solid capabilities in {skills}.",
        "Demonstrates {yoe:.1f} years of experience as a {title}, featuring direct expertise in {skills}.",
        "As a {title} with {yoe:.1f} years of experience, they possess key skills in {skills}."
    ]
    
    # Choose template deterministically based on candidate ID to be reproducible
    cid_num = sum(ord(c) for c in cand.get("candidate_id", ""))
    t_idx = cid_num % len(s1_templates)
    
    if not title:
        title = "Technical Professional"
        
    if skills_str:
        sent1 = s1_templates[t_idx].format(title=title, yoe=yoe, skills=skills_str)
    else:
        sent1 = f"A {title} with {yoe:.1f} years of experience, matching adjacent technical criteria."

    # ── Sentence 2: Activity, Location, Notice, Education, Concerns ───
    s2_parts = []
    
    # Notice Period
    notice = rs.get("notice_period_days")
    if notice is not None:
        if notice <= 15:
            s2_parts.append(f"available on immediate notice ({notice}d)")
        elif notice <= 30:
            s2_parts.append(f"available on short notice ({notice}d)")
        elif notice > 90:
            s2_parts.append(f"has a long notice period of {notice}d")
            
    # Location
    loc_score = score_details.get("loc_score", 0.0)
    loc = profile.get("location", "")
    if loc:
        if loc_score >= 0.9:
            s2_parts.append(f"based in target location ({loc})")
        elif loc_score >= 0.75 and rs.get("willing_to_relocate"):
            s2_parts.append(f"willing to relocate from {loc}")

    # Education
    edu_bonus = score_details.get("edu_bonus", 0.0)
    if edu_bonus >= 0.04:
        s2_parts.append("graduated from a Tier-1 institution")
    elif edu_bonus >= 0.02:
        s2_parts.append("holds a Tier-2 academic degree")

    # Behavioral Availability
    bh = score_details.get("behavioral_score", 0.5)
    otw = rs.get("open_to_work_flag")
    
    beh_signals = []
    if bh >= 0.75:
        beh_signals.append("highly active on the platform")
    elif bh >= 0.55:
        beh_signals.append("good platform activity")
    elif bh <= 0.35:
        beh_signals.append("low platform responsiveness")
        
    if otw is True:
        beh_signals.append("actively seeking roles")
        
    if beh_signals:
        s2_parts.append(" and ".join(beh_signals))

    # Logistical combination
    if s2_parts:
        sent2 = ", ".join(s2_parts[:-1])
        if len(s2_parts) > 1:
            sent2 += f", and {s2_parts[-1]}."
        else:
            sent2 = s2_parts[0] + "."
        sent2 = sent2[0].upper() + sent2[1:]
    else:
        sent2 = "Platform engagement and availability indicators are in the neutral range."

    # ── Sentence 3: Concerns & Penalties ──────────────────────────────
    pens = score_details.get("penalty_reasons", [])
    sent3 = ""
    if pens:
        sent3 = f" Note concern: {pens[0]}."

    return f"{sent1} {sent2}{sent3}"
