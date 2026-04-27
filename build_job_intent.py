import json
import requests
from db import get_local_connection
import os
from dotenv import load_dotenv
load_dotenv()
AWS_BEARER_TOKEN_BEDROCK = os.getenv("AWS_BEARER_TOKEN")
AWS_BEDROCK_MODEL_ID = os.getenv("AWS_BEDROCK_MODEL_ID")

BEDROCK_API_URL = f"https://bedrock-runtime.us-east-1.amazonaws.com/model/{AWS_BEDROCK_MODEL_ID}/invoke"

HEADERS = {
    "Authorization": f"Bearer {AWS_BEARER_TOKEN_BEDROCK}",
    "Content-Type": "application/json"
}
def call_llm_for_intent(semantic_text: str) -> dict:
    prompt = f"""
You are an expert system for understanding messy job descriptions.

Read the provided job text and return ONLY valid JSON with exactly these keys:

{{
  "role_summary": "short summary of the role",
  "core_role": "normalized role name",
  "seniority": "intern/junior/mid/senior/lead/manager/unknown",
  "domain_name": "domain if clear, else unknown",
  "must_have_skills": ["skill1", "skill2"],
  "secondary_skills": ["skill1", "skill2"],
  "responsibilities": ["responsibility1", "responsibility2"],
  "tools": ["tool1", "tool2"],
  "job_intent": "one or two line description of what the company is truly hiring for"
}}

Rules:
- Output raw JSON only
- No markdown
- No explanation
- No extra keys
- Use "unknown" where unclear
- responsibilities must be short action phrases
- tools must be technologies, platforms, frameworks, or enterprise systems
- must_have_skills must contain only real required skills
- secondary_skills must contain nice-to-have or weaker signals

Job text:
{semantic_text}
""".strip()
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        "inferenceConfig": {
            "temperature": 0,
            "maxTokens": 1200
        }
    }

    response = requests.post(
        BEDROCK_API_URL,
        headers=HEADERS,
        json=payload,
        timeout=60
    )

    response.raise_for_status()
    result = response.json()

    output_text = ""

    if "output" in result and "message" in result["output"]:
        content = result["output"]["message"].get("content", [])
        if content and isinstance(content, list):
            output_text = content[0].get("text", "")
    elif "choices" in result:
        output_text = result["choices"][0]["message"]["content"]

    clean_text = output_text.strip()

    if clean_text.startswith("```"):
        clean_text = clean_text.replace("```json", "").replace("```", "").strip()

    try:
     return json.loads(clean_text)
    except Exception:
    # 🔹 attempt recovery: extract JSON block
     try:
        start = clean_text.find("{")
        end = clean_text.rfind("}") + 1
        if start != -1 and end != -1:
            return json.loads(clean_text[start:end])
     except:
        pass

    # 🔹 final fallback (safe default)
    return {}


def normalize_llm_output(llm_result: dict) -> dict:
    # ✅ SAME AS YOUR CODE (unchanged)
    normalized = {
        "role_summary": "",
        "core_role": "unknown",
        "seniority": "unknown",
        "domain_name": "unknown",
        "must_have_skills": [],
        "secondary_skills": [],
        "responsibilities": [],
        "tools": [],
        "job_intent": ""
    }

    if not isinstance(llm_result, dict):
        return normalized

    if "role_summary" in llm_result:
        normalized["role_summary"] = llm_result.get("role_summary", "") or ""
        normalized["core_role"] = llm_result.get("core_role", "unknown") or "unknown"
        normalized["seniority"] = llm_result.get("seniority", "unknown") or "unknown"
        normalized["domain_name"] = llm_result.get("domain_name", "unknown") or "unknown"
        normalized["must_have_skills"] = llm_result.get("must_have_skills", []) or []
        normalized["secondary_skills"] = llm_result.get("secondary_skills", []) or []
        normalized["responsibilities"] = llm_result.get("responsibilities", []) or []
        normalized["tools"] = llm_result.get("tools", []) or []
        normalized["job_intent"] = llm_result.get("job_intent", "") or ""
        return normalized

    return normalized



def build_intent(job_ids: list):

    if not job_ids:
        return {"status": "no_jobs_provided"}

    conn = get_local_connection()
    read_cursor = conn.cursor(dictionary=True)
    write_cursor = conn.cursor()

    format_strings = ','.join(['%s'] * len(job_ids))

    select_query = f"""
    SELECT joborder_id, company_id, semantic_text
    FROM joborder_processed
    WHERE semantic_text IS NOT NULL
      AND TRIM(semantic_text) <> ''
      AND joborder_id IN ({format_strings})
    """

    insert_query = """
    INSERT INTO job_intents (
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
        job_intent,
        raw_llm_output
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        company_id = VALUES(company_id),
        semantic_text = VALUES(semantic_text),
        role_summary = VALUES(role_summary),
        core_role = VALUES(core_role),
        seniority = VALUES(seniority),
        domain_name = VALUES(domain_name),
        must_have_skills = VALUES(must_have_skills),
        secondary_skills = VALUES(secondary_skills),
        responsibilities = VALUES(responsibilities),
        tools = VALUES(tools),
        job_intent = VALUES(job_intent),
        raw_llm_output = VALUES(raw_llm_output)
    """

    read_cursor.execute(select_query, tuple(job_ids))
    rows = read_cursor.fetchall()

    for row in rows:
        joborder_id = row["joborder_id"]
        company_id = row["company_id"]
        semantic_text = row["semantic_text"] or ""

        try:
            llm_result = call_llm_for_intent(semantic_text)
            parsed = normalize_llm_output(llm_result)

            values = (
                joborder_id,
                company_id,
                semantic_text,
                parsed["role_summary"],
                parsed["core_role"],
                parsed["seniority"],
                parsed["domain_name"],
                json.dumps(parsed["must_have_skills"]),
                json.dumps(parsed["secondary_skills"]),
                json.dumps(parsed["responsibilities"]),
                json.dumps(parsed["tools"]),
                parsed["job_intent"],
                json.dumps(llm_result)
            )

            write_cursor.execute(insert_query, values)

        except Exception as e:
            print(f"Failed for joborder_id {joborder_id}: {e}")

    conn.commit()

    read_cursor.close()
    write_cursor.close()
    conn.close()

    return {"status": "intent_done"}