"""
One-shot helper: writes all refactored src/ modules.
Run: python _write_modules.py
"""
import pathlib, textwrap

SRC = pathlib.Path("src")
SRC.mkdir(exist_ok=True)


# ── semantic.py ──────────────────────────────────────────────────────────────
(SRC / "semantic.py").write_text(textwrap.dedent("""\
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity


    def build_candidate_text(cand):
        \"\"\"
        Builds a rich unified text representation of a candidate profile.
        Includes summary, headline, title, ALL career history (title +
        description + industry), education, skills (repeated by proficiency),
        certifications, and skill-assessment names from redrob_signals.
        \"\"\"
        profile = cand.get("profile", {}) or {}
        parts = [
            profile.get("summary", ""),
            profile.get("headline", ""),
            profile.get("current_title", ""),
            profile.get("current_industry", ""),
            profile.get("current_company", ""),
        ]

        for ch in cand.get("career_history", []) or []:
            parts.append(ch.get("title", ""))
            parts.append(ch.get("description", ""))
            parts.append(ch.get("industry", ""))

        for edu in cand.get("education", []) or []:
            parts.append(edu.get("degree", ""))
            parts.append(edu.get("field_of_study", ""))

        for sk in cand.get("skills", []) or []:
            name = sk.get("name", "")
            if not name:
                continue
            repeats = {"expert": 3, "advanced": 2, "intermediate": 1}.get(
                sk.get("proficiency", ""), 1
            )
            parts.extend([name] * repeats)

        for cert in cand.get("certifications", []) or []:
            parts.append(cert.get("name", ""))
            parts.append(cert.get("issuer", ""))

        rs = cand.get("redrob_signals", {}) or {}
        for sk_name in (rs.get("skill_assessment_scores") or {}).keys():
            parts.append(sk_name)

        return " ".join(p for p in parts if p)


    def compute_semantic_scores(candidates, jd_text):
        \"\"\"
        TF-IDF cosine similarity of all candidate texts vs the JD.
        Returns min-max normalised np.ndarray in [0, 1].
        \"\"\"
        if not candidates:
            return np.array([])

        texts = [build_candidate_text(c) for c in candidates]
        corpus = texts + [jd_text]

        vec = TfidfVectorizer(
            max_features=30000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
            min_df=1 if len(corpus) <= 3 else 2,
        )
        try:
            X = vec.fit_transform(corpus)
            sims = cosine_similarity(X[:-1], X[-1]).ravel()
            lo, hi = sims.min(), sims.max()
            if hi - lo < 1e-9:
                return sims
            return (sims - lo) / (hi - lo)
        except Exception:
            return np.zeros(len(candidates))
"""), encoding="utf-8")
print("semantic.py OK")


# ── behavioral.py ─────────────────────────────────────────────────────────────
(SRC / "behavioral.py").write_text(textwrap.dedent("""\
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
        \"\"\"
        Normalised behavioral engagement + availability score in [0, 1].
        Uses ALL redrob_signals fields. Missing fields contribute 0 (neutral).
        Base = 0.50.
        \"\"\"
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
"""), encoding="utf-8")
print("behavioral.py OK")


# ── scoring.py ────────────────────────────────────────────────────────────────
(SRC / "scoring.py").write_text(textwrap.dedent("""\
    from src.skills import compute_skill_score
    from src.title_match import compute_title_score
    from src.experience import compute_experience_score
    from src.behavioral import compute_behavioral_score
    from src.location import compute_location_score
    from src.honeypot import honeypot_score

    # Hybrid scoring weights (sum = 1.0)
    W_SEMANTIC   = 0.30
    W_SKILL      = 0.25
    W_TITLE      = 0.15
    W_EXPERIENCE = 0.10
    W_BEHAVIORAL = 0.10
    W_LOCATION   = 0.05
    W_NOTICE     = 0.05

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
        \"\"\"Small bonus for top-tier academic institutions (generalises across roles).\"\"\"
        best = 0.0
        for edu in candidate.get("education", []) or []:
            tier = edu.get("tier", "")
            best = max(best, _EDU_TIER_BONUS.get(tier, 0.0))
        return best


    def score_candidate(cand, semantic_score, jd_criteria):
        \"\"\"
        Scores a single candidate against parsed JD criteria.

        Args:
            cand           – candidate dict
            semantic_score – TF-IDF cosine sim in [0, 1]
            jd_criteria    – output of parse_job_description()

        Returns dict with 'score' + all component breakdowns.
        \"\"\"
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
            W_SEMANTIC   * semantic_score
            + W_SKILL      * skill_score
            + W_TITLE      * title_score
            + W_EXPERIENCE * exp_score
            + W_BEHAVIORAL * beh_score
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
"""), encoding="utf-8")
print("scoring.py OK")


# ── reasoning.py ──────────────────────────────────────────────────────────────
(SRC / "reasoning.py").write_text(textwrap.dedent("""\
    def build_reasoning(cand, score_details):
        \"\"\"
        Generates a recruiter-style explanation using only real candidate fields.
        No hallucinations — every clause references actual profile data or scores.
        \"\"\"
        profile = cand.get("profile", {}) or {}
        rs      = cand.get("redrob_signals", {}) or {}
        bits    = []

        # 1. Identity opening: title + experience
        title = profile.get("current_title")
        yoe   = profile.get("years_of_experience")
        if yoe is None or yoe < 0:
            total_mo = sum(
                (ch.get("duration_months") or 0)
                for ch in (cand.get("career_history", []) or [])
            )
            yoe = round(total_mo / 12.0, 1) if total_mo > 0 else None

        if title and yoe is not None:
            bits.append(f"{title} with {yoe:.1f} yrs experience")
        elif title:
            bits.append(title)
        elif yoe is not None:
            bits.append(f"Professional with {yoe:.1f} yrs experience")

        # 2. Semantic match strength
        sem = score_details.get("semantic_score", 0.0)
        if sem >= 0.80:
            bits.append("profile is an exceptional semantic match to the JD")
        elif sem >= 0.60:
            bits.append("strong semantic overlap with role requirements")
        elif sem >= 0.40:
            bits.append("moderate semantic alignment with the JD")

        # 3. Matched skills (up to 4)
        matched = score_details.get("matched_core", [])
        if matched:
            show = ", ".join(matched[:4])
            bits.append(f"key skills matched: {show}")

        # 4. Skill assessment scores (platform-verified competency)
        assessments = rs.get("skill_assessment_scores") or {}
        top_assess = sorted(assessments.items(), key=lambda x: -x[1])[:2]
        if top_assess:
            a_str = ", ".join(f"{k} ({v:.0f}/100)" for k, v in top_assess)
            bits.append(f"platform-verified assessments: {a_str}")

        # 5. Behavioral engagement
        bh = score_details.get("behavioral_score", 0.5)
        otw = rs.get("open_to_work_flag")
        if bh >= 0.75:
            bits.append("highly active on platform with strong engagement signals")
        elif bh >= 0.55:
            bits.append("good recruiter responsiveness and platform activity")
        elif bh <= 0.35:
            bits.append("low platform activity — may need outreach")

        if otw is True:
            bits.append("openly seeking new opportunities")
        elif otw is False:
            bits.append("not currently marked open-to-work")

        # 6. Location fit
        loc = profile.get("location", "")
        if loc and score_details.get("loc_score", 0.0) >= 0.9:
            bits.append(f"based in preferred location ({loc})")
        elif score_details.get("loc_score", 0.0) >= 0.75:
            willing = rs.get("willing_to_relocate")
            if willing:
                bits.append(f"willing to relocate ({loc})")

        # 7. Notice period
        notice = rs.get("notice_period_days")
        if notice is not None:
            if notice <= 15:
                bits.append(f"immediately / very short notice ({notice}d)")
            elif notice <= 30:
                bits.append(f"short notice period ({notice}d)")
            elif notice > 90:
                bits.append(f"long notice period ({notice}d) — plan ahead")

        # 8. Education tier
        edu_bonus = score_details.get("edu_bonus", 0.0)
        if edu_bonus >= 0.04:
            bits.append("Tier-1 academic background")
        elif edu_bonus >= 0.02:
            bits.append("Tier-2 academic background")

        # 9. Concerns / penalties
        penalties = score_details.get("penalty_reasons", [])
        if penalties:
            bits.append(f"concern: {penalties[0]}")

        # 10. Honeypot flag
        if score_details.get("is_honeypot"):
            hp_r = score_details.get("honeypot_reasons", [])
            msg  = hp_r[0] if hp_r else "multiple profile inconsistencies detected"
            bits.append(f"FLAGGED — {msg}")

        if not bits:
            return "Candidate evaluated against job criteria — insufficient profile data for detailed reasoning."

        # Join clauses, capitalise, terminate
        text = "; ".join(bits[:6]) + "."
        return text[0].upper() + text[1:]
"""), encoding="utf-8")
print("reasoning.py OK")

print("All modules written successfully.")
