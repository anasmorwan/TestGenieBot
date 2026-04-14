from queue import PriorityQueue

task_queue = PriorityQueue()
delayed_queue = PriorityQueue()



def add_task(task: dict):
    if task.get("run_at"):
        delayed_queue.put((task["run_at"], task))
    else:
        task_queue.put((task.get("priority", 1), task))



def get_task():
    return task_queue.get()
