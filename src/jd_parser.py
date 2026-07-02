import re

try:
    # pyrefly: ignore [missing-import]
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

# Define a comprehensive list of known skills for matching, spanning AI, ML, data engineering, software, cloud, and tools.
KNOWN_SKILLS = {
    # AI & ML
    "embeddings", "sentence transformers", "semantic search", "vector search", "vector representations", "text encoders",
    "information retrieval", "search infrastructure", "search backend", "search & discovery", "indexing algorithms",
    "hugging face transformers", "faiss", "pinecone", "qdrant", "weaviate", "milvus", "opensearch", "elasticsearch",
    "pgvector", "bm25", "haystack", "llamaindex", "rag", "learning to rank", "ranking systems", "recommendation systems",
    "python", "llms", "langchain", "fine-tuning llms", "lora", "qlora", "peft", "prompt engineering", "model adaptation",
    "machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn", "mlops", "mlflow", "feature engineering",
    "statistical modeling", "data science", "nlp", "natural language processing", "document processing", "content matching",
    "open-source ml libraries", "computer vision", "cnn", "image classification", "object detection", "yolo", "opencv",
    "gans", "diffusion models", "asr", "tts", "speech recognition", "reinforcement learning",
    # Data & Analytics
    "sql", "postgresql", "mongodb", "redis", "spark", "airflow", "kafka", "databricks", "data pipelines", "etl",
    "apache beam", "apache flink", "workflow orchestration", "time series", "forecasting", "snowflake", "bigquery", "dbt",
    # Software & Cloud
    "docker", "kubernetes", "kubeflow", "bentoml", "aws", "gcp", "azure", "java", "go", "rust", "rest apis",
    "microservices", "ci/cd", "terraform", "grpc", "html", "css", "javascript", "typescript", "react", "angular",
    "vue.js", "node.js", "next.js", "django", "flask", "fastapi", "spring boot", "graphql", "redux", "webpack", "tailwind",
    # Project & Tools
    "project management", "scrum", "agile", "jira", "git", "github", "tableau", "powerbi"
}

# Seniority mapping
SENIORITIES = ["senior", "lead", "principal", "staff", "junior", "intern", "director", "manager", "head", "associate", "mid"]

# Location keywords to map
LOCATIONS = ["pune", "noida", "bangalore", "bengaluru", "chennai", "hyderabad", "mumbai", "delhi", "gurgaon", "remote", "hybrid", "onsite"]

def parse_job_description(jd_text, candidate_skills_vocab=None):
    """
    Parses a job description text to extract structured parameters.
    Returns:
        dict: {
            "role": str,
            "required_skills": list[str],
            "preferred_skills": list[str],
            "min_experience": int/float,
            "location": str,
            "seniority": str,
            "raw_text": str
        }
    """
    if not jd_text:
        return {
            "role": "Software Engineer",
            "required_skills": [],
            "preferred_skills": [],
            "min_experience": 0,
            "location": "",
            "seniority": "",
            "raw_text": ""
        }
    
    # Try to load spacy blank English model to utilize its sentence tokenizer if available
    sentences = []
    if HAS_SPACY:
        try:
            nlp = spacy.blank("en")
            doc = nlp(jd_text)
            sentences = [sent.text for sent in doc.sents]
        except Exception:
            pass
            
    if not sentences:
        # Fallback to a simple sentence split by punctuation
        sentences = [s.strip() for s in re.split(r'[.!?\n]', jd_text) if s.strip()]

    # 1. Extract Seniority
    seniority = ""
    for word in SENIORITIES:
        if re.search(r'\b' + re.escape(word) + r'\b', jd_text, re.IGNORECASE):
            seniority = word.capitalize()
            break

    # 2. Extract Role / Title
    role = ""
    # Look at the first 3 lines or first sentence for title patterns
    title_candidates = []
    lines = [l.strip() for l in jd_text.split('\n') if l.strip()]
    if lines:
        for line in lines[:3]:
            # If the line is short (under 50 chars) and contains role keywords, it is likely the title
            if len(line) < 60 and any(kw in line.lower() for kw in ["engineer", "developer", "scientist", "manager", "analyst", "specialist"]):
                title_candidates.append(line)
    
    if title_candidates:
        role = title_candidates[0]
    else:
        # Fallback search in first sentence
        first_sent = sentences[0] if sentences else ""
        match = re.search(r'(?:looking for a|hiring for a|role of a)\s+([^,.\n]+)', first_sent, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
        else:
            # Fallback to general term
            role = "AI/ML Engineer" if "ai" in jd_text.lower() or "learning" in jd_text.lower() else "Software Engineer"
    
    # Clean up role string
    role = re.sub(r'^(?:looking for a|hiring a|role of|position of)\s+', '', role, flags=re.IGNORECASE)
    role = role.split(" – ")[0].split(" - ")[0].split(" | ")[0].strip()

    # 3. Extract Experience Requirements
    min_experience = 0
    # Search for patterns like: 5+ years, 3 to 5 years, minimum 4 years
    exp_matches = re.findall(r'(\d+)\s*(?:-|to)?\s*(\d+)?\s*(?:years|yrs|year)\b', jd_text, re.IGNORECASE)
    for match in exp_matches:
        val1 = int(match[0])
        val2 = int(match[1]) if match[1] else val1
        # Take the lower bound of the years range as the minimum required experience
        if val1 > min_experience and val1 < 25:  # avoid absurd numbers
            min_experience = val1
            
    # Also search for "minimum of X years"
    min_exp_match = re.search(r'(?:minimum|at least|req|require|needs)\s*(?:of)?\s*(\d+)\s*(?:years|yrs|year)', jd_text, re.IGNORECASE)
    if min_exp_match:
        val = int(min_exp_match.group(1))
        if val < 25:
            min_experience = max(min_experience, val)

    # 4. Extract Location
    location = ""
    for loc in LOCATIONS:
        if re.search(r'\b' + re.escape(loc) + r'\b', jd_text, re.IGNORECASE):
            location = loc.capitalize()
            break

    # 5. Extract Required & Preferred Skills
    required_skills = []
    preferred_skills = []
    
    # Classify sections of the JD text
    req_sections = []
    pref_sections = []
    
    current_section = "general"
    current_lines = []
    
    for line in jd_text.split('\n'):
        line_clean = line.strip().lower()
        if not line_clean:
            continue
        
        # Check if line indicates a section transition
        is_req = any(kw in line_clean for kw in ["requirements", "what you need", "must have", "essential", "qualifications", "key skills", "core skills"])
        is_pref = any(kw in line_clean for kw in ["preferred", "plus", "nice to have", "highly desired", "bonus", "advantage", "desired"])
        
        if is_req:
            if current_section == "required":
                req_sections.extend(current_lines)
            elif current_section == "preferred":
                pref_sections.extend(current_lines)
            current_section = "required"
            current_lines = []
        elif is_pref:
            if current_section == "required":
                req_sections.extend(current_lines)
            elif current_section == "preferred":
                pref_sections.extend(current_lines)
            current_section = "preferred"
            current_lines = []
        else:
            current_lines.append(line)
            
    # Add trailing section
    if current_section == "required":
        req_sections.extend(current_lines)
    elif current_section == "preferred":
        pref_sections.extend(current_lines)
        
    req_text = " ".join(req_sections).lower()
    pref_text = " ".join(pref_sections).lower()
    full_text_lower = jd_text.lower()
    
    skills_to_search = set(KNOWN_SKILLS)
    if candidate_skills_vocab:
        for s in candidate_skills_vocab:
            if s:
                skills_to_search.add(s.lower().strip())

    # Match skills from skills_to_search in each section
    for skill in skills_to_search:
        if not skill:
            continue
        # Construct lookaround pattern for boundary safety (e.g. C++, .NET, C#)
        start_b = r'\b' if skill[0].isalnum() else r'(?<![a-zA-Z0-9])'
        end_b = r'\b' if skill[-1].isalnum() else r'(?![a-zA-Z0-9])'
        pattern = start_b + re.escape(skill) + end_b
            
        if re.search(pattern, req_text):
            required_skills.append(skill)
        elif re.search(pattern, pref_text):
            preferred_skills.append(skill)
        elif re.search(pattern, full_text_lower):
            # If found but not in specific section, default to required if we don't have clear sections,
            # or put in preferred if we do have a requirements section.
            if len(req_sections) > 0 and len(pref_sections) > 0:
                preferred_skills.append(skill)
            else:
                required_skills.append(skill)
                
    # If no required skills were found, extract capitalized technical-looking terms from bullet points
    if not required_skills:
        for line in jd_text.split('\n'):
            if line.strip().startswith(('-', '*', '•')):
                # Find capitalized terms or alphanumeric symbols
                tech_terms = re.findall(r'\b[A-Z][a-zA-Z0-9\.\-\#\+]*\b', line)
                for term in tech_terms:
                    term_lower = term.lower()
                    if len(term) > 1 and term_lower not in ["the", "and", "for", "with", "this", "our", "you", "are", "will", "have"]:
                        required_skills.append(term_lower)
                        
    # Deduplicate lists
    required_skills = sorted(list(set(required_skills)))
    preferred_skills = sorted(list(set(preferred_skills) - set(required_skills)))
    
    # Capitalize skills for aesthetic representation
    required_skills = [s.title() if s not in ["nlp", "rag", "ml", "ai", "sql", "gcp", "aws", "ci/cd", "etl", "rest apis", "gans", "asr", "tts", "cnn"] else s.upper() for s in required_skills]
    preferred_skills = [s.title() if s not in ["nlp", "rag", "ml", "ai", "sql", "gcp", "aws", "ci/cd", "etl", "rest apis", "gans", "asr", "tts", "cnn"] else s.upper() for s in preferred_skills]

    return {
        "role": role,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "min_experience": min_experience,
        "location": location,
        "seniority": seniority,
        "raw_text": jd_text
    }
