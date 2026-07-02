"""
Semantic-ish similarity without a network call or a GPU.

We deliberately use TF-IDF + cosine rather than a downloaded sentence-
transformers model:
  - submission_spec.md section 3 forbids GPUs and hosted LLM calls during
    the ranking step, and requires the whole thing to run in 5 minutes on
    a CPU-only 16GB box with NO network. A HF model download at ranking
    time would violate "no network during ranking" unless pre-cached, and
    even a cached MiniLM forward pass over 100K free-text profiles adds
    real, hard-to-bound CPU time and dependency risk on unknown grading
    hardware.
  - TF-IDF cosine similarity against a hand-written positive/negative JD
    anchor is fast (<10s for 100K docs), fully deterministic, reproducible
    on any machine, and -- crucially -- easy to defend in a Stage 5
    interview: every ranking decision traces back to a specific word/phrase
    overlap with a document that is checked into the repo.

Candidates are scored on cosine-similarity-to-POSITIVE-anchor minus
cosine-similarity-to-NEGATIVE-anchor, computed within a single TF-IDF space
fit on (candidate texts + both anchors), then min-max normalized to [0,1].
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import config as cfg


def build_candidate_text(cand):
    parts = [cand["profile"].get("summary", ""), cand["profile"].get("headline", "")]
    for ch in cand.get("career_history", [])[:4]:
        parts.append(ch.get("description", ""))
        parts.append(ch.get("title", ""))
    return " ".join(p for p in parts if p)


def compute_semantic_scores(texts):
    """texts: list[str], one per candidate, in stable order.
    Returns np.ndarray in [0,1], same order.
    """
    corpus = texts + [cfg.POSITIVE_ANCHOR, cfg.NEGATIVE_ANCHOR]
    vec = TfidfVectorizer(
        max_features=40000,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=2,
    )
    X = vec.fit_transform(corpus)
    cand_X, pos_vec, neg_vec = X[:-2], X[-2], X[-1]

    pos_sim = cosine_similarity(cand_X, pos_vec).ravel()
    neg_sim = cosine_similarity(cand_X, neg_vec).ravel()

    diff = pos_sim - neg_sim
    lo, hi = diff.min(), diff.max()
    if hi - lo < 1e-9:
        return np.zeros_like(diff)
    return (diff - lo) / (hi - lo)
