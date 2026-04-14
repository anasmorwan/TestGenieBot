from queue import PriorityQueue

task_queue = PriorityQueue()
delayed_queue = PriorityQueue()

def add_task(priority, task: dict):
    task_queue.put((priority, task))


def get_task():
    return task_queue.get()
