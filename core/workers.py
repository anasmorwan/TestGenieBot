import threading
from core.task_queue import task_queue

from services import handlers  # أو أي functions عندك

def worker():
    while True:
        priority, task = task_queue.get()

        try:
            process_task(task)
        finally:
            task_queue.task_done()

def start_workers(n=10):
    for _ in range(n):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
