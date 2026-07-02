"""Streaming loader for candidates.jsonl (and candidates.jsonl.gz).

Never loads the whole 100K-candidate file into a DataFrame of raw JSON --
we stream line by line, extract only the numeric/categorical features we
need into flat dicts, and let scoring run on that. This keeps peak memory
well under the 16 GB budget even on modest laptops.
"""
import gzip
import json


def iter_candidates(path):
    """Yield one parsed candidate dict per line. Supports .jsonl and .jsonl.gz."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
