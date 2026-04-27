#  AI Job Matching System

This project is an end-to-end backend system designed to match job descriptions intelligently using a combination of Large Language Models (LLMs) and semantic embeddings.

Instead of relying on simple keyword matching, the system understands the *meaning* of job descriptions by converting unstructured data into structured insights and vector representations. This allows it to identify genuinely similar roles even when the wording differs significantly.

---

## Problem Statement

Traditional job matching systems depend heavily on keyword overlap. While simple, this approach often fails to capture the actual intent behind a role.

For instance, roles like *Software Engineer* and *Backend Developer* may require nearly identical skills but can be missed due to different wording. Similarly, *Machine Learning Engineer* and *Data Scientist* often overlap in responsibilities but are not matched effectively using keyword-based methods.

The core challenge is transforming messy, unstructured job descriptions into something that can be compared meaningfully.

---

## Solution

This system addresses the problem by combining three key ideas:

* **LLM-based structuring** to extract meaningful information such as role, skills, and responsibilities
* **Embedding-based similarity** to capture semantic relationships between jobs
* **Heuristic refinement** to improve match quality using domain logic like skill overlap and role alignment

By blending structured understanding with semantic similarity, the system produces more accurate and reliable job matches.

---

## System Architecture

The overall flow of the system is designed as a pipeline:

```
Raw Job Data (Database)
        ↓
Data Cleaning & Normalization
        ↓
LLM-Based Intent Extraction
        ↓
Embedding Generation (Sentence Transformers)
        ↓
Similarity Matching API (Cosine Similarity + Heuristics)
```

Each stage transforms the data into a more refined and usable representation.

---

## Pipeline Overview

### 1. Data Ingestion

The system begins by fetching raw job data from a source database. This includes fields such as job title, description, and skills. Only active (non-deleted) jobs are processed, and the system supports incremental processing using specific job IDs instead of reprocessing the entire dataset.

---

### 2. Data Cleaning & Semantic Preparation

Raw job descriptions often contain HTML, repeated phrases, and irrelevant content. This stage removes noise, filters weak or generic sentences, and constructs a clean, meaningful representation called `semantic_text`. This improves the quality of downstream processing.

---

### 3. Intent Extraction (LLM)

Using AWS Bedrock, the system extracts structured information from the cleaned text. This includes:

* Role summary
* Core role
* Seniority level
* Must-have and secondary skills
* Responsibilities
* Tools and technologies
* Overall job intent

This step converts unstructured text into a structured format that is easier to reason about and compare.

---

### 4. Embedding Generation

The system combines multiple signals — including semantic text, skills, role, and intent — into a single representation. This enriched text is then converted into a vector using:

```
sentence-transformers/all-MiniLM-L6-v2
```

These embeddings capture the semantic meaning of each job.

---

### 5. Matching Logic

At query time, the system computes similarity between jobs using cosine similarity on embeddings. It then refines the score using additional logic:

* Penalizes mismatched or weak skill overlap
* Adjusts scores when core roles differ

The final results are ranked and labeled as:

* High Match
* Good Match
* Average Match
* Low Match

---

## 📡 API Endpoints

### 🔹 Process Jobs

**POST /process-jobs**

Processes selected jobs through the full pipeline (cleaning → intent extraction → embedding generation).

**Request:**

```json
{
  "job_ids": [101, 102]
}
```

---

### 🔹 Get Matches

**GET /matches/{job_id}**

Returns the most similar jobs for a given job ID.

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

## Key Design Decisions

* **Hybrid Approach (Structured + Semantic)**
  Instead of embedding raw text directly, the system enriches input using LLM-extracted features to improve representation quality.

* **Dynamic Matching**
  Similarity is computed at runtime rather than precomputed, allowing flexibility and real-time updates.

* **Incremental Processing**
  Jobs are processed selectively using job IDs, avoiding redundant computation and improving efficiency.

---

## Tech Stack

* Python, FastAPI
* MySQL
* Sentence Transformers
* AWS Bedrock (LLM)
* NumPy, scikit-learn

---

## Setup Instructions

```
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## 📈 Future Improvements

* Replace brute-force comparison with vector indexing (e.g., FAISS)
* Learn similarity weights instead of using fixed heuristics
* Add caching for frequently requested matches
* Improve LLM robustness with retry and fallback mechanisms

---

## Key Takeaways

* Combines LLM-based understanding with vector similarity
* Handles noisy, real-world job data effectively
* Designed with incremental and scalable processing in mind
* Demonstrates applied AI system design beyond basic implementations

---

