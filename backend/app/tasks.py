import queue
import threading
import time
import uuid

from app.config import SETTINGS


class TaskManager:
    def __init__(self, max_concurrent=3):
        self.queue = queue.Queue()
        self.max_concurrent = max_concurrent
        self.jobs = {}
        self.lock = threading.Lock()
        self.running = 0
        self.workers = []
        self._start_workers()

    def _start_workers(self):
        for _ in range(self.max_concurrent):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)

    def _worker_loop(self):
        while True:
            payload = self.queue.get()
            if payload is None:
                break

            job_id, handler, params = payload
            self._update_job(job_id, status="running", message="Starting", progress=0)
            with self.lock:
                self.running += 1
            try:
                handler(job_id, params, self._update_job)
                self._update_job(job_id, status="done", progress=100, message="Completed")
            except Exception as exc:
                self._update_job(
                    job_id,
                    status="failed",
                    message="Failed",
                    error=str(exc),
                )
            finally:
                with self.lock:
                    self.running = max(0, self.running - 1)
                self.queue.task_done()

    def submit(self, handler, params):
        job_id = uuid.uuid4().hex
        now = time.time()
        with self.lock:
            self.jobs[job_id] = {
                "id": job_id,
                "status": "queued",
                "message": "Queued",
                "progress": 0,
                "created_at": now,
                "updated_at": now,
                "params": params,
                "output_files": {},
                "previews": {},
                "timeline": [],
                "duration": None,
                "error": None,
            }
        self.queue.put((job_id, handler, params))
        return job_id

    def _update_job(self, job_id, **updates):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            job.update(updates)
            job["updated_at"] = time.time()

    def get(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            return dict(job)

    def list(self):
        with self.lock:
            return [dict(value) for value in self.jobs.values()]

    def get_running_count(self):
        with self.lock:
            return self.running


task_manager = TaskManager(max_concurrent=SETTINGS.task_max_concurrent)
