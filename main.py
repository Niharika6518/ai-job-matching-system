
from fastapi import FastAPI
from db import get_local_connection, get_source_connection
from build_job_embeddings import build_embeddings
from job_processed import process_jobs
from build_job_intent import build_intent

import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()


@app.post("/process-jobs")
def process_pipeline(payload: dict):
    job_ids = payload.get("job_ids", [])

    if not job_ids:
        return {"status": "error", "message": "No job_ids provided"}

    conn = get_local_connection()
    cursor = conn.cursor()

    results = []

    for job_id in job_ids:

       
        source_conn = get_source_connection()
        source_cursor = source_conn.cursor()

        source_cursor.execute(
            "SELECT 1 FROM joborder WHERE joborder_id = %s",
            (job_id,)
        )
        exists_in_source = source_cursor.fetchone()

        source_cursor.close()
        source_conn.close()

        if not exists_in_source:
            results.append({
                "job_id": job_id,
                "status": "not_found_in_source"
            })
            continue

        cursor.execute(
            "SELECT embedding_vector FROM job_embeddings WHERE joborder_id = %s",
            (job_id,)
        )
        existing_embedding = cursor.fetchone()

        if existing_embedding:
            results.append({
                "job_id": job_id,
                "status": "already_processed"
            })
            continue

        try:
     
            process_jobs([job_id])
            build_intent([job_id])
            build_embeddings([job_id])

            results.append({
                "job_id": job_id,
                "status": "processed"
            })

        except Exception as e:
            results.append({
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            })

    cursor.close()
    conn.close()

    return {
        "message": "Processing completed",
        "results": results
    }


@app.get("/matches/{job_id}")
def get_matches(job_id: int):

    conn = get_local_connection()
    cursor = conn.cursor(dictionary=True)

    
    cursor.execute(
        "SELECT embedding_vector FROM job_embeddings WHERE joborder_id = %s",
        (job_id,)
    )
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        return {
            "status": "error",
            "message": "This job_id is not processed"
        }

    target_vector = np.array(json.loads(row["embedding_vector"]))


    cursor.execute("""
    SELECT core_role, must_have_skills
    FROM job_intents
    WHERE joborder_id = %s
    """, (job_id,))
    target_meta = cursor.fetchone()

    skills_target = set()
    role_target = ""

    if target_meta:
        try:
            skills_target = set(json.loads(target_meta.get("must_have_skills") or "[]"))
        except:
            skills_target = set()

        role_target = (target_meta.get("core_role") or "").lower()


    cursor.execute("""
    SELECT 
        e.joborder_id,
        e.company_id,
        e.embedding_vector,
        i.core_role,
        i.must_have_skills
    FROM job_embeddings e
    JOIN job_intents i ON e.joborder_id = i.joborder_id
    WHERE e.embedding_vector IS NOT NULL
    """)
    rows = cursor.fetchall()

    results = []

    for r in rows:
        if r["joborder_id"] == job_id:
            continue

        try:
        
            vector = np.array(json.loads(r["embedding_vector"]))
            score = float(cosine_similarity([target_vector], [vector])[0][0])

            try:
                skills_other = set(json.loads(r.get("must_have_skills") or "[]"))
            except:
                skills_other = set()

            intersection = skills_target.intersection(skills_other)

            if not intersection:
                score *= 0.5
            elif len(intersection) <= 1:
                score *= 0.75

            
            role_other = (r.get("core_role") or "").lower()

            if role_target and role_other and role_target != role_other:
                score *= 0.7

            score_percent = score * 100

            if score_percent >= 90:
                label = "High Match"
            elif score_percent >= 85:
                label = "Good Match"
            elif score_percent >= 75:
                label = "Average Match"
            else:
                label = "Low Match"

            results.append({
                "matched_job_id": r["joborder_id"],
                "score": round(score_percent, 2),
                "label": label
            })

        except Exception:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)

    cursor.close()
    conn.close()

    return {
        "job_id": job_id,
        "total_matches": len(results),
        "matches": results[:10]
    }