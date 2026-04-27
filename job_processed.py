import re
import html
from db import get_source_connection, get_local_connection

def clean_html_text(text: str) -> str:
    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_semantic_text(description: str, skills: str) -> str:
    text = clean_html_text(description).lower()
    skills_text = clean_html_text(skills).lower()

    patterns_to_remove = [
        # section headers
        r"\bproject role\s*:?",
        r"\bproject role description\s*:?",
        r"\bsummary\s*:?",
        r"\broles?\s*&\s*responsibilities\s*:?",
        r"\bprofessional\s*&\s*technical skills\s*:?",
        r"\badditional information\s*:?",

        # education / experience
        r"\bminimum \d+(\.\d+)?\s+year[s]?\b.*",
        r"\b\d+\s+years of full time education\b",

        # repeated corporate phrases
        r"\bexpected to be an sme\b.*",
        r"\bcollaborate(s|d)? with .*",
        r"\bengage(s|d)? with .*",
        r"\bprovide(s|d)? solutions to .*",
        r"\bresponsible for .*",
        r"\bwork(s|ed)? with cross[- ]functional teams.*",
        r"\bcontribute(s|d)? to .*",
        r"\bmentor(s|ed)? .*",
        r"\bcontinuously evaluate and improve .*",

        # generic filler
        r"\bability to .*",
        r"\bstrong understanding of .*",
        r"\bgood knowledge of .*",
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    sentences = re.split(r'[.;]', text)
    filtered = []

    for s in sentences:
        s = s.strip()
        if len(s) < 20:
            continue
        filtered.append(s)

    text = " ".join(filtered)

    semantic_text = f"{text} {skills_text}"
    semantic_text = re.sub(r"\s+", " ", semantic_text).strip()

    return semantic_text

def process_jobs(job_ids: list):

    if not job_ids:
        return

    source_conn = get_source_connection()

    source_cursor = source_conn.cursor(dictionary=True)

    local_conn = get_local_connection()
    local_cursor = local_conn.cursor()


    format_strings = ','.join(['%s'] * len(job_ids))

    select_query = f"""
    SELECT joborder_id, company_id, title, description, skills
    FROM joborder
    WHERE deleted_at IS NULL
    AND joborder_id IN ({format_strings})
    """

    source_cursor.execute(select_query, tuple(job_ids))
    rows = source_cursor.fetchall()

    insert_query = """
    INSERT INTO joborder_processed (
        joborder_id,
        company_id,
        raw_title,
        raw_description,
        raw_skills,
        clean_title,
        clean_description,
        clean_skills,
        combined_clean_text,
        semantic_text
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        company_id = VALUES(company_id),
        raw_title = VALUES(raw_title),
        raw_description = VALUES(raw_description),
        raw_skills = VALUES(raw_skills),
        clean_title = VALUES(clean_title),
        clean_description = VALUES(clean_description),
        clean_skills = VALUES(clean_skills),
        combined_clean_text = VALUES(combined_clean_text),
        semantic_text = VALUES(semantic_text)
    """

    for row in rows:
        joborder_id = row["joborder_id"]
        company_id = row["company_id"]

        raw_title = row["title"] or ""
        raw_description = row["description"] or ""
        raw_skills = row["skills"] or ""

        clean_title = clean_html_text(raw_title)
        clean_description = clean_html_text(raw_description)
        clean_skills = clean_html_text(raw_skills)

        combined_clean_text = " ".join(
            part for part in [clean_title, clean_description, clean_skills] if part
        ).strip()

        semantic_text = build_semantic_text(raw_description, raw_skills)

        values = (
            joborder_id,
            company_id,
            raw_title,
            raw_description,
            raw_skills,
            clean_title,
            clean_description,
            clean_skills,
            combined_clean_text,
            semantic_text
        )

        local_cursor.execute(insert_query, values)

    local_conn.commit()

    source_cursor.close()
    source_conn.close()

    local_cursor.close()
    local_conn.close()
    
    return {"status": "processing_done"}
