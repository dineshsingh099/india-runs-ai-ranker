import difflib
import functools

# Dynamic skill synonym mappings
SYNONYM_GROUPS = [
    # Semantic Search / Retrieval
    {"semantic search", "dense retrieval", "vector search", "information retrieval", "vector representation", "text encoders", "embeddings", "sentence transformers", "information retrieval systems"},
    # Vector Databases
    {"faiss", "pinecone", "qdrant", "weaviate", "milvus", "opensearch", "elasticsearch", "pgvector", "vector database"},
    # RAG / LLM Orchestration
    {"rag", "retrieval augmented generation", "llamaindex", "langchain", "haystack"},
    # LLMs / Transformers
    {"llms", "large language models", "gpt", "transformers", "hugging face", "hugging face transformers", "fine-tuning llms", "lora", "qlora", "peft", "prompt engineering", "model adaptation"},
    # NLP
    {"nlp", "natural language processing", "text mining", "nlp engineer", "computational linguistics", "document processing"},
    # Machine Learning / Deep Learning
    {"machine learning", "ml", "deep learning", "artificial intelligence", "ai", "statistical modeling"},
    # Computer Vision
    {"computer vision", "cnn", "image classification", "object detection", "yolo", "opencv", "gans", "diffusion models"},
    # Speech / Audio
    {"asr", "tts", "speech recognition", "speech-to-text", "text-to-speech"},
    # Data Pipelines / Orchestration
    {"airflow", "spark", "kafka", "databricks", "data pipelines", "etl", "apache beam", "apache flink", "workflow orchestration"},
    # Cloud / DevOps
    {"docker", "kubernetes", "kubeflow", "bentoml", "aws", "gcp", "azure", "terraform", "ci/cd", "microservices"}
]

PROFICIENCY_MULT = {
    "beginner": 0.4,
    "intermediate": 0.6,
    "advanced": 0.85,
    "expert": 1.0
}

def clean_skill_name(s):
    if not s:
        return ""
    # Lowercase and strip whitespace/punctuation
    return "".join(c for c in s.lower() if c.isalnum() or c in " .+-#").strip()

@functools.lru_cache(maxsize=16384)
def are_skills_similar(skill1, skill2):
    s1 = clean_skill_name(skill1)
    s2 = clean_skill_name(skill2)
    
    if not s1 or not s2:
        return False, 0.0
        
    # 1. Exact match
    if s1 == s2:
        return True, 1.0
        
    # 2. Synonym groups check
    for group in SYNONYM_GROUPS:
        if s1 in group and s2 in group:
            return True, 0.95
            
    # 3. Substring containment
    if s1 in s2 or s2 in s1:
        ratio = min(len(s1), len(s2)) / max(len(s1), len(s2))
        if ratio >= 0.5:
            return True, max(0.75, ratio)
            
    # 4. Mathematical pre-filter for fuzzy match (ratio = 2*M / (len1 + len2) <= 2*min_len / sum_len)
    len1, len2 = len(s1), len(s2)
    if (2.0 * min(len1, len2)) / (len1 + len2) < 0.82:
        return False, 0.0
        
    # 5. Fuzzy match ratio (only if mathematically possible)
    ratio = difflib.SequenceMatcher(None, s1, s2).ratio()
    if ratio >= 0.82:
        return True, ratio
        
    return False, 0.0

def match_skill(target_skill, candidate_skills):
    """
    Finds the best match for target_skill among candidate_skills.
    Returns:
        (is_match: bool, similarity: float, candidate_skill_dict: dict)
    """
    best_sim = 0.0
    best_match_dict = None
    
    for cs in candidate_skills:
        cs_name = cs.get("name", "")
        is_sim, sim_val = are_skills_similar(target_skill, cs_name)
        if is_sim and sim_val > best_sim:
            best_sim = sim_val
            best_match_dict = cs
            
    if best_sim > 0:
        return True, best_sim, best_match_dict
    return False, 0.0, None

def compute_skill_score(candidate, required_skills, preferred_skills):
    """
    Computes dynamic required and preferred skill match score with credibility weighting.
    Returns:
        (skill_score: float, matched_skills: list[str], stuffing_penalty: float)
    """
    cand_skills = candidate.get("skills", []) or []
    
    # If both required and preferred list is empty, default to neutral score
    if not required_skills and not preferred_skills:
        return 0.5, [], 0.0
        
    matched_core = []
    
    # Calculate score for required skills
    required_match_sum = 0.0
    for req_s in required_skills:
        found, sim, cs_dict = match_skill(req_s, cand_skills)
        if found and cs_dict:
            prof = cs_dict.get("proficiency", "intermediate")
            prof_mult = PROFICIENCY_MULT.get(prof, 0.6)
            
            dur = cs_dict.get("duration_months")
            if dur is None or dur < 0:
                duration_trust = 0.15
            else:
                duration_trust = min(1.0, dur / 12.0)
                duration_trust = max(duration_trust, 0.15) if dur > 0 else 0.15
                
            ends = cs_dict.get("endorsements", 0) or 0
            endorsement_bonus = min(1.15, 1.0 + 0.01 * min(ends, 15))
            
            credibility = prof_mult * duration_trust * endorsement_bonus
            contrib = sim * credibility
            required_match_sum += contrib
            
            # Keep track of matched core skills for reasoning generator
            matched_core.append(req_s)
            
    required_match = required_match_sum / len(required_skills) if required_skills else 1.0
    
    # Calculate score for preferred skills
    preferred_match_sum = 0.0
    for pref_s in preferred_skills:
        found, sim, cs_dict = match_skill(pref_s, cand_skills)
        if found and cs_dict:
            prof = cs_dict.get("proficiency", "intermediate")
            prof_mult = PROFICIENCY_MULT.get(prof, 0.6)
            
            dur = cs_dict.get("duration_months")
            if dur is None or dur < 0:
                duration_trust = 0.15
            else:
                duration_trust = min(1.0, dur / 12.0)
                duration_trust = max(duration_trust, 0.15) if dur > 0 else 0.15
                
            ends = cs_dict.get("endorsements", 0) or 0
            endorsement_bonus = min(1.15, 1.0 + 0.01 * min(ends, 15))
            
            credibility = prof_mult * duration_trust * endorsement_bonus
            preferred_match_sum += sim * credibility
            
    preferred_match = preferred_match_sum / len(preferred_skills) if preferred_skills else 1.0
    
    skill_score = 0.7 * required_match + 0.3 * preferred_match
    
    # Anti-keyword-stuffing check
    stuffing_penalty = 0.0
    if len(cand_skills) > 15:
        relevant_count = 0
        all_jd_skills = required_skills + preferred_skills
        for cs in cand_skills:
            cs_name = cs.get("name", "")
            is_relevant = False
            for jd_s in all_jd_skills:
                sim_ok, _ = are_skills_similar(cs_name, jd_s)
                if sim_ok:
                    is_relevant = True
                    break
            if is_relevant:
                relevant_count += 1
                
        relevance_ratio = relevant_count / len(cand_skills)
        if relevance_ratio < 0.15:
            stuffing_penalty = 0.20 * (1.0 - relevance_ratio)
            
    return max(0.0, min(1.0, skill_score)), matched_core, stuffing_penalty
