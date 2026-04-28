# AI Job Matching System

An end-to-end backend system that intelligently matches job descriptions using a combination of **LLM-based understanding** and **semantic similarity**.

Unlike traditional keyword-based systems, this solution captures the **true meaning of roles**, enabling accurate matching even when job descriptions are worded differently.

---

# Why this exists

Most job matching systems rely on **keyword overlap**.

That breaks in real scenarios:

* *“Software Engineer” vs “Backend Developer”*
* *“Machine Learning Engineer” vs “Data Scientist”*

Same intent, different wording → poor matches

The real challenge is:

> Converting messy, unstructured job descriptions into something that can be compared meaningfully.

---

# What this system does differently

This system combines three layers:

### 1. LLM-based understanding

Extracts structured meaning from raw job descriptions

### 2. Semantic embeddings

Captures contextual similarity between roles

### 3. Heuristic refinement

Improves match quality using domain logic (skills + role alignment)

Result: **More accurate and meaningful job matches**

---

# System Architecture

```text
Raw Job Data (DB)
        ↓
Cleaning & Normalization
        ↓
LLM Intent Extraction
        ↓
Embedding Generation
        ↓
Similarity Matching API
```

Each stage improves the quality and structure of the data.

---

# Pipeline Breakdown

## 1. Data Ingestion

* Fetches raw job data (title, description, skills)
* Supports **incremental processing** using job IDs

---

## 2. Data Cleaning & Semantic Preparation

* Removes HTML and noise
* Filters generic/low-signal content
* Produces `semantic_text`

Improves downstream model performance

---

## 3. Intent Extraction (LLM)

Using AWS Bedrock, the system extracts:

* Role summary
* Core role
* Seniority
* Must-have & secondary skills
* Responsibilities
* Tools
* Job intent

Converts unstructured text → structured understanding

---

## 4. Embedding Generation

Combines multiple signals:

* semantic_text
* skills
* tools
* role
* intent

Then generates embeddings using:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Produces rich semantic vectors

---

## 5. Matching Logic

* Computes **cosine similarity**
* Applies domain-aware adjustments:

### Skill-based adjustment

* No overlap → penalized
* Weak overlap → reduced score

### ✔ Role-based adjustment

* Different core roles → score reduced

---

### 📊 Match Labels

* **90+** → High Match
* **85–90** → Good Match
* **75–85** → Average Match
* **<75** → Low Match

---

#  Async Processing (Scalable Design)

To handle large workloads efficiently, the system uses **background task processing**:

### Flow:

```text
POST /start-processing → create task
        ↓
Worker picks task → processes in batches
        ↓
GET /task-status → track progress
```

Prevents API timeouts
Handles thousands of jobs reliably

---

# 📡 API Endpoints

## 🔹 Start Processing (Async)

```http
POST /start-processing
```

**Request:**

```json
{
  "job_ids": [101, 102]
}
```

**Response:**

```json
{
  "task_id": "abc-123",
  "status": "queued"
}
```

---

## 🔹 Task Status

```http
GET /task-status/{task_id}
```

**Response:**

```json
{
  "status": "processing",
  "processed": 50,
  "total": 200,
  "progress": 25.0
}
```

---

## 🔹 Get Matches

```http
GET /matches/{job_id}
```

**Response:**

```json
{
  "job_id": 101,
  "total_matches": 50,
  "matches": [
    {
      "matched_job_id": 202,
      "score": 91.2,
      "label": "High Match"
    }
  ]
}
```

---

## 🔹 (Legacy) Direct Processing

```http
POST /process-jobs
```

Synchronous — use only for small batches/testing

---

# Tech Stack

* **Backend:** FastAPI
* **Database:** MySQL
* **LLM:** AWS Bedrock
* **Embeddings:** Sentence Transformers
* **ML Tools:** NumPy, scikit-learn

---

# 🛠 Setup

```bash
pip install -r requirements.txt
uvicorn main:app --reload
python worker.py
```

---

#  Key Design Decisions

### Hybrid Intelligence (LLM + Embeddings)

Instead of raw text embeddings, the system enriches input with structured signals → better semantic representation.

---

### Dynamic Matching

Similarity is computed at runtime → flexible and up-to-date results.

---

### Incremental Processing

Processes only required job IDs → avoids redundant computation.

---

### Async Architecture

Decouples API from processing → scalable and production-ready.

---

#  Future Improvements

* Replace brute-force matching with **FAISS / vector DB**
* Introduce **learned scoring instead of fixed heuristics**
* Add **LLM caching & batching**
* Improve **explainability (why jobs matched)**
* Parallelize worker for faster processing

Just tell me 👍
