import argparse
import csv
import time
import os
from src.data_loader import iter_candidates
from src.pipeline import rank_candidates

DEFAULT_JD = """
Role: Senior AI Engineer
Location: Pune or Noida, India
Experience: 5+ years of experience

We are looking for a Senior AI Engineer to design and implement production-grade embeddings-based retrieval and ranking systems at scale. You will own the search infrastructure, semantic search, vector databases (FAISS, Pinecone, Qdrant), and hybrid retrieval combining dense and sparse search.

Requirements:
- 5+ years of experience in AI/ML, NLP, and Information Retrieval.
- Proven expertise in Python, PyTorch, LangChain, RAG, and LLM fine-tuning.
- Solid hands-on experience building search systems, dense retrieval, and database index optimization.
- Located in or willing to relocate to Pune or Noida.

Preferred:
- Experience with MLOps, vector search engineering, and deploying large language models.
"""

def main():
    ap = argparse.ArgumentParser(description="Rank candidates against a job description.")
    ap.add_argument("--candidates", default="data/candidates.jsonl", help="Path to candidate jsonl file")
    ap.add_argument("--jd", default=None, help="Path to Job Description text file or raw JD text string")
    ap.add_argument("--out", default="outputs/submission.csv", help="Path to output submission CSV")
    args = ap.parse_args()

    t0 = time.time()

    # 1. Resolve Job Description
    jd_text = DEFAULT_JD
    if args.jd:
        if os.path.exists(args.jd):
            with open(args.jd, "r", encoding="utf-8") as f:
                jd_text = f.read()
            print(f"Loaded Job Description from file: {args.jd}")
        else:
            jd_text = args.jd
            print("Using raw text provided via --jd as Job Description.")
    else:
        print("No Job Description specified. Using default Senior AI Engineer JD.")

    # 2. Load candidates
    print("Loading candidates...")
    if not os.path.exists(args.candidates):
        print(f"Error: Candidate file not found at {args.candidates}")
        return
        
    candidates = list(iter_candidates(args.candidates))
    print(
        f"Loaded {len(candidates)} candidates in "
        f"{time.time() - t0:.1f}s"
    )

    t1 = time.time()

    # 3. Score and Rank
    print("Scoring and ranking candidates...")
    top = rank_candidates(
        candidates,
        jd_text,
        top_n=100  # always extract top 100 for final submission
    )

    print(
        f"Scoring completed in "
        f"{time.time() - t1:.1f}s"
    )

    hp_in_top = sum(
        1 for r in top if r["is_honeypot"]
    )

    print(
        f"Honeypots in top 100: "
        f"{hp_in_top} ({hp_in_top / 100.0:.1%})"
    )

    # 4. Write submission.csv
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(
        args.out,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:
        writer = csv.writer(f)

        writer.writerow(
            ["candidate_id", "rank", "score", "reasoning"]
        )

        for r in top:
            writer.writerow([
                r["candidate_id"],
                r["rank"],
                r["score"],
                r["reasoning"]
            ])
            
    print(f"Wrote {len(top)} rows to {args.out}")
    print(
        f"Total runtime: {time.time() - t0:.1f}s"
    )

if __name__ == "__main__":
    main()