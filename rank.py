import argparse
import csv
import time
import config as cfg
from src.data_loader import iter_candidates
from src.pipeline import rank_candidates

def main():
      ap = argparse.ArgumentParser()
      ap.add_argument("--candidates", default="data/candidates.jsonl")
      ap.add_argument("--out", default="outputs/submission.csv")
      args = ap.parse_args()

      t0 = time.time()

      print("Loading candidates...")
      candidates = list(iter_candidates(args.candidates))
      print(
         f"Loaded {len(candidates)} candidates in "
         f"{time.time() - t0:.1f}s"
      )

      t1 = time.time()

      print("Scoring and ranking candidates...")
      top = rank_candidates(
         candidates,
         top_n=cfg.TOP_N
      )

      print(
         f"Scoring completed in "
         f"{time.time() - t1:.1f}s"
      )

      hp_in_top = sum(
         1 for r in top if r["is_honeypot"]
      )

      print(
         f"Honeypots in top {cfg.TOP_N}: "
         f"{hp_in_top} ({hp_in_top / cfg.TOP_N:.1%})"
      )

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