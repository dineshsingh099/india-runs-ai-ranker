import gzip
import json

def iter_candidates(path):
    """Yield one parsed candidate dict. Supports JSON arrays, JSONL files, and gzipped versions.
    
    Ensures memory safety by peeking at the format first: streaming line-by-line for JSONL,
    and fallback loading for JSON arrays.
    """
    opener = gzip.open if str(path).endswith(".gz") else open
    
    # Peek at the first non-empty line's first character to determine the format
    first_char = ""
    try:
        with opener(path, "rt", encoding="utf-8") as f:
            for line in f:
                line_stripped = line.strip()
                if line_stripped:
                    first_char = line_stripped[0]
                    break
    except Exception:
        pass

    if first_char == "[":
        # Process as standard JSON array (e.g. sample_candidates.json)
        with opener(path, "rt", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    yield data
                elif isinstance(data, list):
                    for item in data:
                        yield item
            except Exception as e:
                print(f"Error parsing JSON array: {e}")
    else:
        # Process as JSONL line-by-line (e.g. candidates.jsonl)
        with opener(path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Skip bracket-only lines in case it's a hybrid/poorly-formatted JSON
                if line == "[" or line == "]":
                    continue
                if line.endswith(","):
                    line = line[:-1].strip()
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue  # ignore corrupt rows to ensure robustness on unseen datasets
