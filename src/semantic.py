import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def build_candidate_text(cand):
    """
    Builds a rich unified text representation of a candidate profile.
    Includes summary, headline, title, ALL career history (title +
    description + industry), education, skills (repeated by proficiency),
    certifications, and skill-assessment names from redrob_signals.
    """
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

def compute_tfidf_scores(candidates, jd_text):
    """
    TF-IDF cosine similarity of all candidate texts vs the JD.
    Returns min-max normalised np.ndarray in [0, 1].
    """
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

def compute_dense_scores(candidates, jd_text, model_path="./models/all-MiniLM-L6-v2"):
    """
    SentenceTransformer dense embedding cosine similarity of candidate texts vs the JD.
    Loads offline model from model_path, falling back to TF-IDF on error.
    """
    if not candidates:
        return np.array([])
        
    try:
        from sentence_transformers import SentenceTransformer
        # Check if local model path exists and is populated
        if os.path.exists(model_path) and any(os.listdir(model_path)):
            model = SentenceTransformer(model_path)
        else:
            model = SentenceTransformer("all-MiniLM-L6-v2")
            
        texts = [build_candidate_text(c) for c in candidates]
        
        # Encode candidate profiles and job description
        cand_embs = model.encode(texts, show_progress_bar=False, batch_size=64, convert_to_numpy=True)
        jd_emb = model.encode([jd_text], show_progress_bar=False, convert_to_numpy=True)
        
        # Compute cosine similarity
        sims = cosine_similarity(cand_embs, jd_emb).ravel()
        lo, hi = sims.min(), sims.max()
        if hi - lo < 1e-9:
            return sims
        return (sims - lo) / (hi - lo)
    except Exception as e:
        print(f"Dense scoring failed: {e}. Falling back to TF-IDF.")
        return compute_tfidf_scores(candidates, jd_text)

def compute_semantic_scores(candidates, jd_text, use_dense=False, model_path="./models/all-MiniLM-L6-v2"):
    """
    Main interface for semantic scoring.
    """
    if use_dense:
        return compute_dense_scores(candidates, jd_text, model_path)
    else:
        return compute_tfidf_scores(candidates, jd_text)
