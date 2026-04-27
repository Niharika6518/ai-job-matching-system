
import json
from sentence_transformers import SentenceTransformer
from db import get_local_connection

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def build_embedding_text(row: dict) -> str:
    semantic_text = row.get("semantic_text") or ""
    role_summary = row.get("role_summary") or ""
    core_role = row.get("core_role") or ""
    job_intent = row.get("job_intent") or ""

    must_have_skills = row.get("must_have_skills") or "[]"
    secondary_skills = row.get("secondary_skills") or "[]"
    responsibilities = row.get("responsibilities") or "[]"
    tools = row.get("tools") or "[]"

    try:
        must_have_skills = json.loads(must_have_skills)
    except Exception:
        must_have_skills = []

    try:
        secondary_skills = json.loads(secondary_skills)
    except Exception:
        secondary_skills = []

    try:
        responsibilities = json.loads(responsibilities)
    except Exception:
        responsibilities = []

    try:
        tools = json.loads(tools)
    except Exception:
        tools = []

    parts = [

     f"semantic text: {semantic_text}" if semantic_text else "",
     f"must have skills: {', '.join(map(str, must_have_skills))}" if must_have_skills else "",
     f"tools: {', '.join(map(str, tools))}" if tools else "",
     f"secondary skills: {', '.join(map(str, secondary_skills))}" if secondary_skills else "",
     f"core role: {core_role}" if core_role else "",
     f"job intent: {job_intent}" if job_intent else "",
     f"role summary: {role_summary}" if role_summary else "",
     f"responsibilities: {', '.join(map(str, responsibilities))}" if responsibilities else ""]   

    return " ".join(part for part in parts if part).strip()



def build_embeddings(job_ids: list):

    if not job_ids:
        return {"status": "no_jobs_provided"}

    
    local_conn = get_local_connection()
    read_cursor = local_conn.cursor(dictionary=True)
    write_cursor = local_conn.cursor()

    format_strings = ','.join(['%s'] * len(job_ids))

    select_query = f"""
    SELECT
    joborder_id,
    company_id,
    semantic_text,
    role_summary,
    core_role,
    seniority,
    domain_name,
    must_have_skills,
    secondary_skills,
    responsibilities,
    tools,
    job_intent
FROM job_intents
    WHERE core_role IS NOT NULL
      AND TRIM(core_role) <> ''
      AND job_intent IS NOT NULL
      AND TRIM(job_intent) <> ''
      AND joborder_id IN ({format_strings})
    """

    insert_query = """
    INSERT INTO job_embeddings (
        joborder_id,
        company_id,
        embedding_text,
        embedding_vector
    )
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        company_id = VALUES(company_id),
        embedding_text = VALUES(embedding_text),
        embedding_vector = VALUES(embedding_vector)
    """

    read_cursor.execute(select_query, tuple(job_ids))
    rows = read_cursor.fetchall()

    for row in rows:
        joborder_id = row["joborder_id"]
        company_id = row["company_id"]

        embedding_text = build_embedding_text(row)

        if not embedding_text:
            continue

        try:
         vector = model.encode(embedding_text).tolist()
        except Exception:
         continue

        values = (
            joborder_id,
            company_id,
            embedding_text,
            json.dumps(vector)
        )

        write_cursor.execute(insert_query, values)

    local_conn.commit()

    read_cursor.close()
    write_cursor.close()
    local_conn.close()

    return {"status": "embedding_done"}

