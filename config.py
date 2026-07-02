"""
Configuration derived directly from job_description.docx, redrob_signals_doc.docx
and empirical analysis of candidates.jsonl (closed vocab: 47 titles, 133 skills,
28 locations). Every weight below is justified in README.md / the PPT deck.
"""

# ---------------------------------------------------------------------------
# 1. TITLE TIERS
# current_title (and past titles in career_history) are matched against this
# tier map. This is the single strongest anti-keyword-stuffing signal: the
# sample_submission.csv provided by the organizers literally ranks an
# "HR Manager" #1 because she lists 9 AI keywords as skills -- that is the
# trap the redrob_signals_doc + job_description explicitly warn about.
# ---------------------------------------------------------------------------
TITLE_TIER = {
    # Tier 5 -- exact core (weight 1.00)
    "Senior AI Engineer": 1.00, "Lead AI Engineer": 1.00,
    "Staff Machine Learning Engineer": 1.00, "Senior Machine Learning Engineer": 1.00,
    "Applied ML Engineer": 1.00, "Machine Learning Engineer": 1.00,
    "AI Engineer": 1.00, "Search Engineer": 1.00,
    "Recommendation Systems Engineer": 1.00, "Senior NLP Engineer": 1.00,
    "NLP Engineer": 1.00, "Senior Data Scientist": 1.00,
    # Tier 4 -- strong (weight 0.80)
    "ML Engineer": 0.80, "AI Research Engineer": 0.80, "Data Scientist": 0.80,
    "Senior Software Engineer (ML)": 0.80, "Computer Vision Engineer": 0.70,
    "AI Specialist": 0.75,
    # Tier 3 -- junior AI (weight 0.55)
    "Junior ML Engineer": 0.55,
    # Tier 2 -- adjacent production engineering, could pivot in (weight 0.32)
    "Senior Data Engineer": 0.32, "Senior Software Engineer": 0.32,
    "Backend Engineer": 0.32, "Data Engineer": 0.30, "Analytics Engineer": 0.28,
    "Data Analyst": 0.22, "Software Engineer": 0.28,
    # Tier 1 -- weak adjacent (weight 0.12)
    "Cloud Engineer": 0.12, "DevOps Engineer": 0.12, "Full Stack Developer": 0.12,
    "Java Developer": 0.10, ".NET Developer": 0.10, "Frontend Engineer": 0.08,
    "Mobile Developer": 0.08, "QA Engineer": 0.10,
    # Tier 0 -- non-fit / keyword-stuffer trap territory (weight 0.00)
    "Business Analyst": 0.0, "HR Manager": 0.0, "Mechanical Engineer": 0.0,
    "Accountant": 0.0, "Project Manager": 0.0, "Customer Support": 0.0,
    "Operations Manager": 0.0, "Content Writer": 0.0, "Sales Executive": 0.0,
    "Civil Engineer": 0.0, "Graphic Designer": 0.0, "Marketing Manager": 0.0,
}
DEFAULT_TITLE_WEIGHT = 0.05  # unseen/unknown title -> tiny benefit of doubt

# ---------------------------------------------------------------------------
# 2. SKILL TAXONOMY
# The dataset intentionally contains rare *synonym* skill labels
# (e.g. "Vector Representations", "Search Backend", "Text Encoders",
# "Information Retrieval Systems") that mean the same thing as common labels
# ("Embeddings", "Vector Search"). A pure exact-keyword ranker would miss
# these -- exactly the "Tier 5 candidate who doesn't say RAG or Pinecone"
# trap the JD calls out. So core/strong skills are grouped by meaning, not
# by string.
# ---------------------------------------------------------------------------
SKILL_WEIGHTS = {
    # CORE: embeddings, semantic retrieval, vector DB / hybrid search (weight 3.0)
    "Embeddings": 3.0, "Sentence Transformers": 3.0, "Semantic Search": 3.0,
    "Vector Search": 3.0, "Vector Representations": 3.0, "Text Encoders": 3.0,
    "Information Retrieval": 3.0, "Information Retrieval Systems": 3.0,
    "Search Infrastructure": 3.0, "Search Backend": 3.0, "Search & Discovery": 3.0,
    "Indexing Algorithms": 3.0, "Hugging Face Transformers": 2.5,
    "FAISS": 3.0, "Pinecone": 3.0, "Qdrant": 3.0, "Weaviate": 3.0, "Milvus": 3.0,
    "OpenSearch": 3.0, "Elasticsearch": 3.0, "pgvector": 3.0, "BM25": 3.0,
    "Haystack": 3.0, "LlamaIndex": 2.8, "RAG": 2.8,
    "Learning to Rank": 3.0, "Ranking Systems": 3.0, "Recommendation Systems": 3.0,
    # STRONG: general applied-ML / LLM / eval fundamentals (weight 2.0)
    "Python": 2.0, "LLMs": 2.0, "LangChain": 1.5, "Fine-tuning LLMs": 2.0,
    "LoRA": 1.8, "QLoRA": 1.8, "PEFT": 1.8, "Prompt Engineering": 1.5,
    "Model Adaptation": 2.0, "Machine Learning": 2.0, "Deep Learning": 2.0,
    "PyTorch": 2.0, "TensorFlow": 1.8, "scikit-learn": 1.6, "MLOps": 1.6,
    "MLflow": 1.4, "Feature Engineering": 1.6, "Statistical Modeling": 1.4,
    "Data Science": 1.4, "NLP": 2.0, "Natural Language Processing": 2.0,
    "Document Processing": 1.8, "Content Matching": 1.8, "Open-source ML libraries": 1.5,
    # MODERATE: production/infra & data engineering (weight 0.8)
    "Docker": 0.8, "Kubernetes": 0.8, "Kubeflow": 0.8, "BentoML": 0.8,
    "Spark": 0.6, "Airflow": 0.6, "Kafka": 0.6, "Databricks": 0.6,
    "Data Pipelines": 0.6, "ETL": 0.5, "Apache Beam": 0.5, "Apache Flink": 0.5,
    "Reinforcement Learning": 1.2, "Workflow Orchestration": 0.6,
    "Time Series": 0.6, "Forecasting": 0.5,
    # WEAK-ADJACENT: computer vision / speech (JD: relevant only w/ NLP too)
    "CNN": 0.4, "Computer Vision": 0.4, "Image Classification": 0.4,
    "Object Detection": 0.4, "YOLO": 0.3, "OpenCV": 0.3, "GANs": 0.4,
    "Diffusion Models": 0.4, "ASR": 0.3, "TTS": 0.3, "Speech Recognition": 0.3,
    # WEAK: generic production/cloud engineering (small credibility bump)
    "AWS": 0.25, "GCP": 0.25, "Azure": 0.25, "SQL": 0.3, "PostgreSQL": 0.2,
    "MongoDB": 0.15, "Redis": 0.15, "Java": 0.15, "Go": 0.2, "Rust": 0.2,
    "REST APIs": 0.15, "Microservices": 0.2, "CI/CD": 0.2, "Terraform": 0.15,
    "gRPC": 0.15, "Snowflake": 0.15, "BigQuery": 0.15, "dbt": 0.15,
    # Everything else defaults to 0.0 (Accounting, Sales, Marketing, SEO,
    # Six Sigma, Tally, SAP, Photoshop, Illustrator, Figma, PowerPoint, Excel,
    # Project Management, Scrum, Agile, Content Writing, React, Angular,
    # Vue.js, HTML, CSS, TypeScript, JavaScript, Node.js, Next.js, Django,
    # Flask, FastAPI, Spring Boot, GraphQL, Redux, Webpack, Tailwind,
    # Salesforce CRM, Hadoop -- these are noise for an AI-ranking role and
    # deliberately score 0 so they cannot inflate a mismatched profile.
}
PROFICIENCY_MULT = {"beginner": 0.4, "intermediate": 0.6, "advanced": 0.85, "expert": 1.0}
MAX_SKILL_RAW_SCORE = 14.0  # empirical cap for normalization (a genuine Tier-5 profile)

# ---------------------------------------------------------------------------
# 3. TEXT ANCHORS for TF-IDF semantic scoring (career descriptions + summary)
# Positive anchor = paraphrase of what the JD says the *ideal* candidate did.
# Negative anchor = paraphrase of the JD's explicit disqualifiers.
# ---------------------------------------------------------------------------
POSITIVE_ANCHOR = """
Shipped a production embeddings based retrieval and ranking system used by
real users at scale. Owns the intelligence layer deciding what recruiters
and candidates see, hybrid retrieval combining dense and sparse search,
built and operated vector database infrastructure, handled embedding drift
and index refresh and retrieval quality regression in production. Designed
offline and online evaluation frameworks for ranking systems, NDCG, MRR,
MAP, offline to online correlation, A/B testing interpretation. Wrote
production quality Python code, still writes code today, not only
architecture. Worked at a product company, not only a services or
consulting company. Strong opinions on hybrid versus dense retrieval and
when to fine-tune versus prompt an LLM, backed by systems actually built.
Mentors engineers, works closely with product managers, ships fast,
iterates from real user feedback, has years of pre LLM era search and
ranking experience, understood retrieval and ranking before it was
fashionable.
"""

NEGATIVE_ANCHOR = """
Purely academic research lab experience with no production deployment,
published papers only, never shipped a system to real users. Entire recent
AI experience is under twelve months old and consists of calling OpenAI
through LangChain with no substantial pre LLM era production ML experience.
Senior engineer who moved into architecture or tech lead role and has not
written production code in the last eighteen months. Career trajectory
shows title chasing, switching companies every one point five years,
optimizing for senior staff principal titles. GitHub full of LangChain
tutorials and blog posts about demos built with the latest hot framework,
thinks about frameworks not systems. Entire career spent only at large IT
services consulting companies without any product company experience.
Primary expertise is computer vision or speech or robotics with no
meaningful natural language processing or information retrieval exposure.
Five or more years on entirely closed source proprietary systems with zero
external validation, no papers, no talks, no open source contributions.
"""

CONSULTING_FIRMS = {"TCS", "Infosys", "Wipro", "Accenture", "Cognizant", "Capgemini"}

# ---------------------------------------------------------------------------
# 4. LOCATION FIT
# ---------------------------------------------------------------------------
PRIMARY_LOCATIONS = {"Pune", "Noida"}
TIER1_INDIA_CITIES = {
    "Bangalore", "Mumbai", "Delhi", "Chennai", "Hyderabad", "Pune", "Noida",
    "Gurgaon",  # Delhi NCR
}
OTHER_INDIA_CITIES_PENALTY = 0.55   # still India, not explicitly preferred
NON_INDIA_PENALTY_BASE = 0.20       # "case-by-case, no visa sponsorship"

# ---------------------------------------------------------------------------
# 5. FINAL SCORE WEIGHTS (documented + defended in README.md)
# ---------------------------------------------------------------------------
W_TITLE = 0.30
W_SKILL = 0.24
W_SEMANTIC = 0.18
W_EXPERIENCE = 0.10
W_LOCATION = 0.06
W_NOTICE = 0.04
# behavioral modifier is MULTIPLICATIVE on top of the additive sum, range ~[0.72, 1.15]
# disqualifier penalties are ADDITIVE (negative) on top of the additive sum

TOP_N = 100
