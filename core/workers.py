import threading
from core.task_queue import task_queue
from bot.bot_instance import mybot
from bot.handlers import file_hanlder, text_handler, image_handler  # أو أي functions عندك



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

def process_task(task):
    task_type = task["type"]

    if task["type"] == "new_updates":
        update = task["update"]

        msg = update.get("message")
        if not msg:
            return

        if "text" in msg:
            handle_text(user_id, msg["text"], msg)

        elif "document" in msg:
            handle_file(user_id, msg["document"], msg)

        elif "photo" in msg:
            handle_photo(user_id, msg["photo"], msg)
        

    elif task_type == "generate_exam":
        handlers.generate_exam(task)

    elif task_type == "ai_request":
        handlers.ai_request(task)

    elif task_type == "send_message":
        handlers.send_message(task)

