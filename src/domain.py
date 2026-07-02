DOMAINS = {
    "Search": {
        "search", "retrieval", "elasticsearch", "opensearch", "solr", "faiss", "pinecone", 
        "qdrant", "weaviate", "milvus", "hybrid search", "semantic search", "vector search", 
        "information retrieval", "bm25", "lucene", "index", "re-ranking", "indexing", 
        "vector representations", "text encoders", "embeddings", "sentence transformers", 
        "information retrieval systems"
    },
    "ML": {
        "machine learning", "ml", "deep learning", "ai", "artificial intelligence", "nlp", 
        "natural language processing", "computer vision", "transformers", "hugging face", 
        "hugging face transformers", "fine-tuning llms", "lora", "qlora", "peft", 
        "prompt engineering", "model adaptation", "pytorch", "tensorflow", "scikit-learn", 
        "neural", "keras"
    },
    "Backend": {
        "backend", "software engineer", "swe", "developer", "python", "java", "go", "rust", 
        "c++", "django", "flask", "fastapi", "spring boot", "apis", "microservices", 
        "database", "postgresql", "mysql", "redis"
    },
    "Frontend": {
        "frontend", "ui", "ux", "javascript", "typescript", "react", "angular", "vue", 
        "html", "css", "tailwind"
    },
    "Data Engineering": {
        "data engineer", "data engineering", "pipelines", "etl", "spark", "airflow", 
        "kafka", "databricks", "data pipelines", "snowflake", "bigquery", "dbt", "data warehouse"
    },
    "Cloud": {
        "cloud", "aws", "gcp", "azure", "docker", "kubernetes", "kubeflow", "bentoml", 
        "terraform"
    },
    "DevOps": {
        "devops", "ci/cd", "jenkins", "ansible", "prometheus", "grafana"
    }
}

def extract_jd_domain_weights(jd_text):
    """
    Scans the JD text for domain keywords to calculate target domain weights.
    """
    text = jd_text.lower()
    weights = {}
    for dom, kws in DOMAINS.items():
        # count occurrences of keywords in the JD
        count = sum(1 for kw in kws if kw in text)
        if count > 0:
            weights[dom] = count
            
    total = sum(weights.values())
    if total == 0:
        return {"ML": 1.0}  # default fallback
        
    return {dom: w / total for dom, w in weights.items()}

def extract_candidate_domains(cand):
    profile = cand.get("profile", {}) or {}
    history = cand.get("career_history", []) or []
    skills = cand.get("skills", []) or []
    
    # build a large text block representing candidate background
    texts = [
        profile.get("current_title", ""),
        profile.get("headline", ""),
        profile.get("summary", ""),
    ]
    for ch in history:
        texts.append(ch.get("title", ""))
        texts.append(ch.get("description", ""))
        
    cand_text = " ".join(t for t in texts if t).lower()
    cand_domain_counts = {dom: 0 for dom in DOMAINS}
    
    # Check in text
    for dom, kws in DOMAINS.items():
        for kw in kws:
            if kw in cand_text:
                cand_domain_counts[dom] += 1
                
    # Check in skill names specifically (stronger weight)
    for sk in skills:
        s_name = sk.get("name", "").lower()
        if not s_name:
            continue
        for dom, kws in DOMAINS.items():
            if s_name in kws or any(kw in s_name for kw in kws):
                cand_domain_counts[dom] += 2
                
    return cand_domain_counts

def compute_domain_score(candidate, jd_domain_weights):
    """
    Computes candidate's domain alignment against Job Description's domain weights.
    Returns float in [0, 1].
    """
    cand_counts = extract_candidate_domains(candidate)
    
    score = 0.0
    for dom, weight in jd_domain_weights.items():
        count = cand_counts.get(dom, 0)
        # 3+ matches represents full domain coverage
        match_ratio = min(1.0, count / 3.0)
        score += weight * match_ratio
        
    return score
