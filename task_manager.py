import json
import uuid
from db import get_local_connection


def create_task(job_ids: list):
    conn = get_local_connection()
    cursor = conn.cursor()

    task_id = str(uuid.uuid4())

    insert_query = """
    INSERT INTO job_tasks (task_id, status, job_ids, total_jobs, processed_jobs)
    VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(insert_query, (
        task_id,
        "pending",
        json.dumps(job_ids),
        len(job_ids),
        0
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return task_id


def get_task(task_id: str):
    conn = get_local_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM job_tasks WHERE task_id = %s", (task_id,))
    task = cursor.fetchone()

    cursor.close()
    conn.close()

    return task


def update_task_status(task_id: str, status: str):
    conn = get_local_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE job_tasks SET status = %s WHERE task_id = %s",
        (status, task_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


def update_progress(task_id: str, processed_jobs: int):
    conn = get_local_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE job_tasks SET processed_jobs = %s WHERE task_id = %s",
        (processed_jobs, task_id)
    )

    conn.commit()
    cursor.close()
    conn.close()