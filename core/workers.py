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
        if not quizzes or len(quizzes) == 0:
            print(f"DEBUG: [User: {user_id}] Quiz generation returned EMPTY result.", flush=True)
            bot.send_message(chat_id, "❌ فشل توليد الاختبار. تأكد أن النص يحتوي على معلومات كافية.")
            return

        if state == "scheduled_quiz":
            quiz_code = store_quiz(user_id, quizzes, schedule=True)
            bot.send_message(
                chat_id=chat_id,
                text=get_message("SCHEDULED_QUIZ_READY"),
                parse_mode="HTML"
            )
            return
        quiz_code = store_quiz(user_id, quizzes)
                    
        maybe_cleanup()
        quiz_len = len(quizzes)

        action = random.choice(["delete", "edit"])
        reply_markup = quiz_keyboard(quiz_code)
        if action == "delete":
            bot.delete_message(chat_id, message_id=waiting_msg.message_id)
            bot.send_message(
                chat_id=chat_id,
                text=get_message("QUIZ_CREATED", count=quiz_len),
                parse_mode="HTML"
            )
            time.sleep(2)
        else:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=get_message("QUIZ_CREATED", count=quiz_len),
                parse_mode="HTML"
                )
            time.sleep(2)
            
        if not quiz_manager.start_quiz(chat_id, quiz_code, bot, is_shared_user=False):
            bot.edit_message_text(
            chat_id=chat_id,
            message_id=waiting_msg.message_id,
            text="😵 لم يتم العثور على هذا الاختبار أو انتهت صلاحيته."
        )

    elif task_type == "file_generate_quiz":
        maybe_cleanup() 
        if not quizzes:
            bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text="❌ فشل تحليل النص أو توليد الأسئلة.")
            return

        if state == "scheduled_quiz":
            quiz_code = store_quiz(user_id, quizzes, schedule=True)
            bot.send_message(
                chat_id=chat_id,
                text=get_message("SCHEDULED_QUIZ_READY"),
                parse_mode="HTML"
            )
            return
        else:
            quiz_code = store_quiz(user_id, quizzes)

        quiz_len = len(quizzes)
        reply_markup = quiz_keyboard(quiz_code)
            
        action = random.choice(["delete", "edit"])
        if action == "delete":
            bot.delete_message(chat_id, message_id=waiting_msg.message_id)
            bot.send_message(
                chat_id=chat_id,
                text=get_message("QUIZ_CREATED", count=quiz_len),
                parse_mode="HTML"
            )
            time.sleep(2)
        else:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=waiting_msg.message_id,
                text=get_message("QUIZ_CREATED", count=quiz_len),
                parse_mode="HTML"
                )
            time.sleep(2)
        quiz_manager.start_quiz(chat_id, quiz_code, bot, is_shared_user=False)
            

    elif task_type == "extend_generate_quiz":
        quiz_manager.generate_and_store(user_id=user_id, msg_id=msg_id, chat_id=user_id, only_generate=only_generate, bot=mybot)


    elif task["type"] == "delayed_message":
        delay = task["delay"]
        time.sleep(delay)
        bot.send_message(task["user_id"], task["text"])



add_task(1, {
                "type": "file_generate_quiz",
                "user_id": user_id,
                "text": content,
                "msg_id": msg_id
            })
