from datetime import date

def _parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None

def get_start_date(job):
    sd = _parse_date(job.get("start_date"))
    if sd:
        return sd
    return date(1970, 1, 1)

def get_seniority_level(title):
    if not title:
        return 0
    t = title.lower()
    
    # Check for Intern / Fresher / Trainee / Graduate
    if any(w in t for w in ["intern", "fresher", "trainee", "graduate"]):
        return 1
        
    # Check for Junior / Associate / Analyst
    if any(w in t for w in ["junior", "jr", "associate", "analyst"]):
        return 2
        
    # Check for Principal / Staff / Architect / Chief / Director / VP / Head / Founder / CTO
    if any(w in t for w in ["principal", "staff", "architect", "chief", "director", "head", "founder", "cto", "vp", "president"]):
        return 5
        
    # Check for Senior / Sr / Lead / Manager
    if any(w in t for w in ["senior", "sr", "lead", "manager"]):
        return 4
        
    # Default mid-level / engineer / developer / specialist / scientist
    return 3

def compute_progression_score(candidate):
    """
    Evaluates career progression and stability.
    Returns a score in [0, 1].
    - Baseline is 0.5.
    - Promoted internally or progressively over time: +bonus.
    - Stability bonus for long tenures: +bonus.
    - Title inflation / suspicious jumps or too frequent changes: -penalty.
    """
    history = candidate.get("career_history", []) or []
    if not history:
        return 0.5
        
    # Sort chronologically (oldest to newest)
    try:
        sorted_history = sorted(history, key=get_start_date)
    except Exception:
        sorted_history = history
    
    levels = [get_seniority_level(job.get("title", "")) for job in sorted_history]
    tenures = [job.get("duration_months", 0) or 0 for job in sorted_history]
    
    score = 0.5
    
    # 1. Promotions / progression
    promotions = 0
    demotions = 0
    for i in range(1, len(levels)):
        if levels[i] > levels[i-1] and levels[i-1] > 0:
            promotions += 1
        elif levels[i] < levels[i-1] and levels[i] > 0:
            demotions += 1
            
    score += promotions * 0.12
    score -= demotions * 0.08
    
    # 2. Tenure stability
    valid_tenures = [t for t in tenures if t > 0]
    if valid_tenures:
        avg_tenure = sum(valid_tenures) / len(valid_tenures)
        if avg_tenure >= 36:
            score += 0.15  # highly loyal / stable
        elif avg_tenure >= 24:
            score += 0.08
        elif avg_tenure < 12:
            score -= 0.15  # job-hopper / high turnover
        elif avg_tenure < 18:
            score -= 0.08
            
    # 3. YOE alignment check for title inflation
    yoe = candidate.get("profile", {}).get("years_of_experience", 0) or 0
    if len(levels) > 0:
        final_level = levels[-1]
        if final_level >= 5 and yoe < 4:
            score -= 0.20
        elif final_level >= 4 and yoe < 2:
            score -= 0.15

    return max(0.0, min(1.0, score))
