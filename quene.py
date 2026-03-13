import os
import sqlite3
# quene


# إعداد قائمة الانتظار والتحكم
request_queue = queue.Queue(maxsize=200)
semaphore = threading.Semaphore(5)
num_workers = 5



def save_request(msg, db_path='requests.db'):
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cur = conn.cursor()
        file_id = getattr(getattr(msg, "document", None), "file_id", None)
        cur.execute(
            'INSERT INTO requests (user_id, username, file_id, status) VALUES (?, ?, ?, ?)',
            (msg.from_user.id, msg.from_user.username or "", file_id, 'pending')
        )
        conn.commit()
    except Exception:
        logging.exception("save_request failed")
    finally:
        try: conn.close()
        except: pass

def update_request_status(file_id, new_status, db_path='requests.db'):
    try:
        if not file_id:
            return
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cur = conn.cursor()
        cur.execute('UPDATE requests SET status=? WHERE file_id=?', (new_status, file_id))
        conn.commit()
    except Exception:
        logging.exception("update_request_status failed")
    finally:
        try: conn.close()
        except: pass



# دالة العامل
def worker():
    while True:
        item = request_queue.get()
        try:
            if isinstance(item, tuple) and len(item) == 2:
                msg, sent_msg = item
                process_message(msg, message_id=sent_msg.message_id, chat_id=sent_msg.chat.id)
            else:
                # عنصر واحد: فقط الرسالة
                msg = item
                process_message(msg)
        except Exception:
            logging.exception("[WORKER ERROR]")
        finally:
            request_queue.task_done()


# تشغيل العمال في الخلفية
def start_workers():
    for _ in range(num_workers):
        threading.Thread(target=worker, daemon=True).start()
    logging.info("Workers started: %s", num_workers)



# بدء البوت
start_workers()