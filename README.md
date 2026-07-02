# Dynamic AI Candidate Ranker — Redrob India.Runs Challenge

This repository contains a production-ready, fully modular, and dataset-agnostic **AI Candidate Ranking System** built for the Redrob India.Runs Data & AI Challenge.

The system ranks candidates the way an expert recruiter would—by actually understanding job descriptions, matching skills and titles semantically, validating career histories, analyzing behavioral availability signals, and relegating mismatched or bad-faith (honeypot) profiles.

---

## 🏗️ Architecture Layout

```
Job Description
      ↓
[jd_parser.py] (Extracts title, skills, experience, location)
      ↓
[semantic.py] (Fits TF-IDF & Cosine Similarity on candidate text vs JD text)
      ↓
[skills.py] ── [title_match.py] ── [experience.py] ── [location.py] ── [behavioral.py] ── [honeypot.py]
      ↓                 ↓                 ↓                ↓                ↓               ↓
(Skill Coverage)  (Title Match)     (YOE Match)     (Location Fit)   (Activity Mod)  (Inconsistencies)
      └─────────────────┴─────────────────┼────────────────┴────────────────┘               │
                                          ↓                                                 │
                                  [scoring.py] (Hybrid Combination)                         │
                                          ↓                                                 │
                                   Honeypot Gated? ◄────────────────────────────────────────┘
                                   ├── Yes ──► Force Score <= 0.03
                                   └── No  ──► Keep Raw Score
                                          ↓
                                  [reasoning.py] (Generate recruiter-style explanation)
                                          ↓
                                  [pipeline.py] (Sort by Score desc, Candidate ID asc)
                                          ↓
                                   Outputs Top 100 ──► submission.csv
```

### File-by-File Responsibilities
- `app.py`: Beautiful Streamlit web interface with a JD text area, parsed preview, candidate upload, interactive score breakdown, and CSV download.
- `rank.py`: CLI script supporting custom job description text files or raw string arguments (falls back to a default Senior AI Engineer JD).
- `validate_submission.py`: Checks submission CSV files for compliance with the challenge rules.
- `src/`
  - `jd_parser.py`: Extracts target title, seniority, min experience, location, and required/preferred skills from raw JD text.
  - `semantic.py`: Performs offline TF-IDF cosine similarity of candidates' profiles and histories against the JD.
  - `skills.py`: Handles synonym expansions, fast length-ratio filters, fuzzy skill matching, and detects skill stuffing.
  - `title_match.py`: Calculates Jaccard & sequence matching for titles, maps common seniority abbreviations, and gates non-technical title keyword stuffers.
  - `experience.py`: Compares candidate years of experience to the JD requirements with career-duration fallback if missing.
  - `location.py`: Computes city, relocate readiness, and country level matching dynamically.
  - `behavioral.py`: Normalizes candidate platform signals (open-to-work status, recruiter response rate, activity date).
  - `scoring.py`: Orchestrates all component scores into a weighted combination and handles penalties.
  - `reasoning.py`: Generates recruiter explanations from factual candidate data fields without hallucinations.
  - `honeypot.py`: Evaluates profile consistency to identify mock profiles.
  - `data_loader.py`: Handles both standard JSON arrays and JSONL streaming for memory efficiency.

---

## 🎯 Generalization & Anti-Overfitting Strategy

This system is built to generalize perfectly to **unseen grading datasets, hidden candidates, and future roles**:

1. **Dataset-Agnostic Processing**: No candidate IDs, specific companies, hardcoded titles, or static weights are hardcoded. Everything is derived dynamically.
2. **Zero-Dependency NLP Fallbacks**: Spacy sentence segmentation falls back gracefully to standard punctuation regex splits if Spacy or its models are absent.
3. **Neutral Missing-Value Handling**: If any candidate profile fields, career histories, or platform signals are missing, they receive neutral defaults (e.g. 0.5 score) and will not crash the ranking engine.
4. **Fuzzy & Synonym-Based Skill Mapping**: Unseen skills are normalized and evaluated via a synonym group lookup. If not in the taxonomy, a fast character length-ratio constraint filters candidate skills, and only potential matches are processed via fuzzy sequence similarity.
5. **Anti-Keyword-Stuffing Gating**: 
   - **Title Mismatch**: Candidates with purely non-technical current titles (e.g., HR, Sales) applying for technical roles are flagged and given a severe penalty.
   - **Skill Stuffing**: Candidates listing more than 15 skills where less than 15% are relevant to the JD are penalized.
   - **Honeypot Relegation**: Inconsistent profiles (e.g. 8 years experience at a company founded 3 years ago, or expert skills with 0 months duration) are detected and relegated to a maximum score of `0.03`, removing them from the top 100 shortlist.

---

## 📈 Hybrid Scoring Weights

Scores are normalized between `[0, 1]` and combined additively:

| Component | Weight | Rationale |
| :--- | :--- | :--- |
| **Semantic Similarity** | `30%` | Holistic alignment of candidate profile summary/career history against JD. |
| **Skill Match** | `25%` | Match rate of required (70%) and preferred (30%) skills, weighted by credibility (duration & level). |
| **Title Fit** | `15%` | Dynamic alignment of current/past titles with target title. |
| **Experience Match** | `10%` | Fit of candidate experience against min JD years (linear penalty for shortfall). |
| **Behavioral Activity** | `10%` | Platform freshness, response rates, and intent to work. |
| **Location Fit** | `5%` | Preferred city matches, relocation flags, and country-level alignment. |
| **Notice Period** | `5%` | Proximity to immediate availability (tapers off as notice exceeds 30/60/90 days). |

---

## ⚡ Execution Instructions

The project runs completely offline and does not require an active internet connection or GPU resources.

### Installation
Ensure you have the required packages:
```bash
pip install -r requirements.txt
```

### CLI Execution
Run the ranker using the command line:
```bash
# Using default JD (Senior AI Engineer)
python rank.py --candidates data/candidates.jsonl --out outputs/submission.csv

# Using custom JD text file
python rank.py --candidates data/candidates.jsonl --jd path/to/jd.txt --out outputs/submission.csv
```

### Streamlit Web UI
Run the interactive dashboard:
```bash
streamlit run app.py
```

### Submission Validation
Validate formatting compliance of any generated CSV:
```bash
python validate_submission.py outputs/submission.csv
```