import time
import json
from db import get_local_connection
from job_processed import process_jobs
from build_job_intent import build_intent
from build_job_embeddings import build_embeddings
from task_manager import update_task_status, update_progress


BATCH_SIZE = 50


def fetch_pending_task():
    conn = get_local_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM job_tasks WHERE status = 'pending' LIMIT 1"
    )

    task = cursor.fetchone()

    cursor.close()
    conn.close()

    return task


def run_worker():
    print("Worker started...")

    while True:
        task = fetch_pending_task()

        if not task:
            time.sleep(5)
            continue

        task_id = task["task_id"]
        job_ids = json.loads(task["job_ids"])

        print(f"Processing task {task_id}")

        try:
            update_task_status(task_id, "processing")

            processed = 0

            for i in range(0, len(job_ids), BATCH_SIZE):
                batch = job_ids[i:i + BATCH_SIZE]

                process_jobs(batch)
                build_intent(batch)
                build_embeddings(batch)

                processed += len(batch)
                update_progress(task_id, processed)

            update_task_status(task_id, "completed")
            print(f"Task {task_id} completed")

        except Exception as e:
            print(f"Task failed: {e}")
            update_task_status(task_id, "failed")


if __name__ == "__main__":
    run_worker()