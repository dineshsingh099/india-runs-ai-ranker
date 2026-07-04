# 🚀 Dynamic AI Candidate Ranker — Redrob India.Runs Challenge

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Offline](https://img.shields.io/badge/Works-Offline-success)

A production-ready, modular, dataset-agnostic AI Candidate Ranking System built for the **Redrob India.Runs Data & AI Challenge**.

## 🌐 Live Demo

**Hugging Face Space**

https://huggingface.co/spaces/dineshsingh07/india-runs-ai-ranker

---

# ✨ Features

- Dynamic Job Description parsing
- Semantic candidate matching (TF-IDF + Cosine Similarity)
- Skill matching with synonym support
- Title similarity scoring
- Experience validation
- Location matching
- Behavioral signal analysis
- Honeypot candidate detection
- Recruiter-style reasoning generation
- Offline execution
- Streamlit dashboard
- CLI support
- CSV submission generation

---

# 🏗️ System Architecture

> Replace the image below with your architecture diagram.

```text
Job Description
      │
      ▼
JD Parser
      │
      ▼
Semantic Matching
      │
 ┌────┼────────────────────────────┐
 ▼    ▼        ▼        ▼          ▼
Skills Title Experience Location Behavioral
 └──────────────┬─────────────────┘
                ▼
        Honeypot Detection
                ▼
         Hybrid Scoring
                ▼
 Recruiter Reasoning Engine
                ▼
 Ranked Candidates (CSV)
```

---

# 📁 Project Structure

```text
india-runs-ai-ranker/
│
├── app.py
├── rank.py
├── validate_submission.py
├── requirements.txt
├── README.md
├── data/
├── outputs/
├── docs/
└── src/
    ├── behavioral.py
    ├── data_loader.py
    ├── experience.py
    ├── honeypot.py
    ├── jd_parser.py
    ├── location.py
    ├── reasoning.py
    ├── scoring.py
    ├── semantic.py
    ├── skills.py
    └── title_match.py
```

---

# 🚀 Getting Started

## 1. Clone Repository

```bash
git clone https://github.com/<your-username>/india-runs-ai-ranker.git
```

## 2. Enter Project

```bash
cd india-runs-ai-ranker
```

## 3. Create Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Run Streamlit

```bash
streamlit run app.py
```

---

# 💻 Run CLI

```bash
python rank.py --candidates data/candidates.jsonl --out outputs/submission.csv
```

With custom Job Description:

```bash
python rank.py --candidates data/candidates.jsonl --jd path/to/jd.txt --out outputs/submission.csv
```

---

# ✅ Validate Submission

```bash
python validate_submission.py outputs/submission.csv
```

---

# 📊 Hybrid Scoring

| Component | Weight |
|-----------|--------|
| Semantic Similarity | 30% |
| Skill Match | 25% |
| Title Match | 15% |
| Experience | 10% |
| Behavioral Signals | 10% |
| Location | 5% |
| Notice Period | 5% |

---

# 📦 Output

The system generates:

```
outputs/submission.csv
```

containing the ranked Top-100 candidates.

---

# 🔮 Future Improvements

- Transformer-based embeddings
- LLM-powered recruiter explanations
- Multi-language resume support
- Explainable AI dashboards
- Cloud deployment

---

# 👨‍💻 Author

**Dinesh Singh**

AI & Data Science Engineer

Hugging Face:
https://huggingface.co/spaces/dineshsingh07/india-runs-ai-ranker
