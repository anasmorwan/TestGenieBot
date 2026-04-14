import threading
from core.task_queue import task_queue, delayed_queue
from bot.bot_instance import mybot
from bot.handlers import file_hanlder, text_handler, image_handler  # أو أي functions عندك
from services.quiz_service import generate_quizzes_from_text
from services.quiz_session_service import quiz_manager




def worker():
    while True:
        priority, task = task_queue.get()

        try:
            process_task(task)
        finally:
            task_queue.task_done()


def delayed_worker():
    while True:
        run_at, task = delayed_queue.get()

        now = time.time()
        if now < run_at:
            time.sleep(run_at - now)

        process_task(task)


def start_workers(n=30):
    for _ in range(n):
        t1 = threading.Thread(target=delayed_worker, daemon=True)
        t2 = threading.Thread(target=worker, daemon=True)
        t1.start()
        t2.start()
        

def process_task(task):
    task_type = task["type"]
    user_id = task["user_id"] if user_id else None
    text = task["text"] if text else None
    msg_id = task["msg_id"] if msg_id else None
    only_generate = task["only_generate"] if only_generate else None 

    if task["type"] == "new_updates":
        update = task["update"]
        mybot.process_new_updates([update])

      
        text_handler.register(mybot)
        file_hanlder.register(mybot)
        image_handler.register(mybot)
        

    elif task_type == "text_generate_quiz": 
        generate_quizzes_from_text(task)

    elif task_type == "file_generate_quiz":
        generate_quizzes_from_text(content=text, user_id=user_id, bot=mybot, msg_id=msg_id)

    elif task_type == "extend_generate_quiz":
        quiz_manager.generate_and_store(user_id=user_id, msg_id=msg_id, chat_id=user_id, only_generate=only_generate, bot=mybot)


    elif task["type"] == "delayed_message":
        delay = task["delay"]
        time.sleep(delay)
        bot.send_message(task["user_id"], task["text"])

