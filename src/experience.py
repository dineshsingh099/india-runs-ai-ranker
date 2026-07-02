def compute_experience_score(candidate, min_experience):
    """
    Compares candidate's years of experience to JD's minimum experience.
    If years_of_experience is missing, it estimates it from the career history.
    
    Returns:
        float: experience match score in [0, 1]
    """
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience")
    
    # Fallback to sum of career history duration_months if yoe is missing or null
    if yoe is None or yoe < 0:
        career_history = candidate.get("career_history", []) or []
        total_months = sum(ch.get("duration_months", 0) or 0 for ch in career_history)
        if total_months > 0:
            yoe = total_months / 12.0
        else:
            yoe = None
            
    # If it is still missing or we get an empty/neutral value, give a neutral score (0.5)
    if yoe is None:
        return 0.5
        
    # If the JD specifies no minimum experience, or min_experience is 0, give full score
    if min_experience <= 0:
        return 1.0
        
    if yoe >= min_experience:
        return 1.0
        
    # Otherwise, return a proportional score
    return max(0.0, yoe / min_experience)
