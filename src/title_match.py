import re
import difflib
import functools

# Title synonyms and mappings
TITLE_SYNONYMS = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "swe": "software engineer",
    "dev": "developer",
    "qa": "quality assurance",
    "db": "database",
    "retrieval": "search",
    "searcher": "search",
    "deeplearning": "machine learning"
}

# Non-technical / non-fit title keywords
NON_TECH_KEYWORDS = {
    "hr", "human resources", "recruiter", "marketing", "sales", "finance", "accountant", "accounting", 
    "mechanical", "civil", "graphic", "content writer", "operations", "project manager", "scrum master",
    "product owner", "sales executive", "customer support", "helpdesk"
}

# Technical keywords
TECH_KEYWORDS = {
    "engineer", "developer", "scientist", "architect", "programmer", "coder", "analyst", "specialist", 
    "technical", "researcher", "lead", "head"
}

def clean_title(title):
    if not title:
        return ""
    # Lowercase and replace non-alphanumeric chars with spaces
    t = re.sub(r'[^a-z0-9]', ' ', title.lower()).strip()
    
    # Expand abbreviations
    words = t.split()
    expanded_words = [TITLE_SYNONYMS.get(w, w) for w in words]
    return " ".join(expanded_words)

def extract_seniority(title_clean):
    seniority_keywords = {
        "senior": ["senior", "sr", "lead", "principal", "staff", "chief", "director", "head", "expert"],
        "junior": ["junior", "jr", "associate", "intern", "fresher", "trainee"],
        "mid": ["mid"]
    }
    
    for level, kw_list in seniority_keywords.items():
        if any(kw in title_clean.split() for kw in kw_list):
            return level
    return "mid"  # default mid-level if no keyword is found

@functools.lru_cache(maxsize=16384)
def title_similarity_score(cand_title, jd_role):
    """
    Computes a similarity score [0, 1] between candidate title and JD role.
    """
    t_cand = clean_title(cand_title)
    t_jd = clean_title(jd_role)
    
    if not t_cand or not t_jd:
        return 0.0
        
    # Check if candidate title is an exact match
    if t_cand == t_jd:
        return 1.0
        
    # Check if the JD role is technical and the candidate title is non-technical
    jd_is_tech = any(kw in t_jd for kw in TECH_KEYWORDS)
    cand_words = set(t_cand.split())
    cand_is_non_tech = any(kw in cand_words for kw in NON_TECH_KEYWORDS)
    
    # Gating: If JD is technical but candidate has a purely non-technical title, score is 0.0
    if jd_is_tech and cand_is_non_tech:
        return 0.0
        
    # Remove seniority words for core title matching
    seniority_words = {"senior", "sr", "lead", "principal", "staff", "junior", "jr", "associate", "intern", "mid", "head", "director"}
    t_cand_core = " ".join([w for w in t_cand.split() if w not in seniority_words])
    t_jd_core = " ".join([w for w in t_jd.split() if w not in seniority_words])
    
    # Core title exact match (e.g. "Senior Machine Learning Engineer" <=> "Machine Learning Engineer")
    if t_cand_core == t_jd_core:
        return 0.90
        
    # Check word overlap
    cand_words = set(t_cand_core.split())
    jd_words = set(t_jd_core.split())
    
    if not cand_words or not jd_words:
        return 0.0
        
    overlap = cand_words & jd_words
    union = cand_words | jd_words
    jaccard = len(overlap) / len(union) if union else 0.0
    
    # Use SequenceMatcher fuzzy similarity ratio with length pre-filter
    len1, len2 = len(t_cand_core), len(t_jd_core)
    max_ratio = (2.0 * min(len1, len2)) / (len1 + len2) if (len1 + len2) > 0 else 0.0
    
    if max_ratio < 0.40:
        fuzzy_ratio = 0.0
    else:
        fuzzy_ratio = difflib.SequenceMatcher(None, t_cand_core, t_jd_core).ratio()
    
    # Hybrid similarity score
    score = 0.5 * jaccard + 0.5 * fuzzy_ratio
    
    # Bonus for role category matches
    categories = [
        {"machine learning", "ml", "artificial intelligence", "ai", "data scientist", "deep learning", "nlp", "computer vision"},
        {"software", "swe", "backend", "frontend", "full stack", "developer", "engineer", "programmer"},
        {"data engineer", "data pipelines", "analytics engineer", "database"}
    ]
    for cat in categories:
        if any(c_word in t_cand_core for c_word in cat) and any(j_word in t_jd_core for j_word in cat):
            score = max(score, 0.65)
            break
            
    # Seniority alignment factor
    cand_seniority = extract_seniority(t_cand)
    jd_seniority = extract_seniority(t_jd)
    
    if jd_seniority == "senior" and cand_seniority == "junior":
        score *= 0.7  # down-weight junior candidates for senior roles
    elif jd_seniority == "junior" and cand_seniority == "senior":
        score *= 0.9  # slight down-weight for overqualification
        
    return max(0.0, min(1.0, score))

def compute_title_score(candidate, jd_role):
    """
    Combines current and past title similarities.
    Returns:
        (title_score: float, current_title_similarity: float)
    """
    profile = candidate.get("profile", {})
    current_title = profile.get("current_title", "")
    
    current_sim = title_similarity_score(current_title, jd_role)
    
    past_titles = [ch.get("title", "") for ch in candidate.get("career_history", [])]
    past_sims = [title_similarity_score(pt, jd_role) for pt in past_titles if pt]
    best_past_sim = max(past_sims, default=0.0)
    
    # Reward candidate with strong current title, but give credit for relevant past history
    title_score = 0.7 * current_sim + 0.3 * best_past_sim
    
    return max(0.0, min(1.0, title_score)), current_sim
