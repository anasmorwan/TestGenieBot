import sqlite3
from storage.sqlite_db import get_connection
import json
from datetime import datetime
from models.quiz import QuizQuestion
# from services.poll_service import send_quiz_poll
import threading
from services.usage import is_paid_user_active
from storage.messages import get_message
from bot.keyboards.upsell_keyboard import quiz_number_limit_upsell
from storage.quiz_attempts import log_quiz_attempt

class QuizManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        
        # ✅ هذا هو الناقص
        self.poll_map = {}

    def start_quiz(self, chat_id, quiz_code, bot, is_shared_user=None):
        print("QUIZ CODE:", quiz_code, flush=True)
        quiz_data = self.load_quiz(quiz_code)
        print("LOADED QUIZ:", quiz_data, flush=True)
        if not quiz_data:
            print("❌ No quiz data", flush=True)
            return False

    
        questions = []
        for q in quiz_data:
            obj = QuizQuestion.from_raw(q)
            print("RAW:", q, flush=True)
            print("PARSED:", obj, flush=True)
            if obj:
                questions.append(obj)

        
        print("TOTAL QUESTIONS:", len(questions))

        if not questions:
            print("❌ No questions", flush=True)
            return False

        
        
        with self.lock:
            self.sessions[chat_id] = {
                "questions": questions,
                "index": 0,
                "score": 0,
                "quiz_code": quiz_code,
                "is_shared_user": is_shared_user   # ✅ أضف هذا السطر
            }
        
        
        self.send_current_question(chat_id, bot, is_shared_user=None)

        return True

    def load_quiz(self, quiz_code):
        with self.lock:
            conn = get_connection()
            c = conn.cursor()

            c.execute(
                "SELECT quiz_data FROM user_quizzes WHERE quiz_code=?",
                (quiz_code,)
            )

            row = c.fetchone()
            conn.close()

            if not row:
                return None

            return json.loads(row[0])
    

    def send_current_question(self, chat_id, bot, is_shared_user=None):
        with self.lock:
            state = self.sessions.get(chat_id)

        if not state:
            print("No quiz session found for chat:", chat_id)
            return

        if state["index"] >= len(state["questions"]):
            print("Index out of range for chat:", chat_id)
            return


        q = state["questions"][state["index"]]
        print(f"Sending question {state['index']+1} to chat {chat_id}")

        self.send_quiz_poll(bot, chat_id, q)

    def handle_answer(self, chat_id, selected_option, bot, is_shared_user=None):
        state = self.sessions.get(chat_id)
        if not state:
            return

        # إذا لم يُمرر is_shared_user كمعامل، نقرأه من الجلسة
        shared = state.get("is_shared_user") if is_shared_user is None else is_shared_user

        q = state["questions"][state["index"]]

        if selected_option == q.correct_index:
            state["score"] += 1

        state["index"] += 1

        if state["index"] >= len(state["questions"]):
            score = state["score"]
            quiz_code = state["quiz_code"]
            total = len(state["questions"])
            log_quiz_attempt(chat_id, quiz_code, score, total)
            self.finish_quiz(chat_id, bot, is_shared_user=shared)

        
        else:
            self.send_current_question(chat_id, bot)
         
    def finish_quiz(self, chat_id, bot, is_shared_user=None):
        
        
        state = self.sessions.pop(chat_id, None)
        if not state:
            return

        score = state["score"]
        total = len(state["questions"])
        total = len(state["questions"])
        score = state.get("score", 0)  # تأكد من وجود score
        
        # إذا لم تُمرر القيمة، نستخدم المخزنة في الجلسة (احتياطي)
        shared = is_shared_user if is_shared_user is not None else state.get("is_shared_user")

        # بناء النص الأساسي
        text = f"انتهى الاختبار\n\nالنتيجة: {score}/{total}"

        # تحديد لوحة المفاتيح حسب حالة المستخدم
        keyboard = None

        if not is_paid_user_active(chat_id) and not shared:
            extra_quiz_msg = get_message("QUIZ_LIMIT")
            if extra_quiz_msg:  # تأكد أن الرسالة موجودة
                text += f"\n\n{extra_quiz_msg}"
            keyboard = quiz_number_limit_upsell()
            # لا تعيد تعريف text هنا
        else:
            # المستخدم مدفوع - لا نضيف شيء
            keyboard = None
            
        # إرسال الرسالة مع التحقق
        try:
            if keyboard:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                # بدون keyboard
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="HTML"
                )
            print(f"✅ تم إرسال النتيجة للمستخدم {chat_id}")
        except Exception as e:
            print(f"❌ فشل إرسال النتيجة: {e}")
            bot.send_message(chat_id, f"خطأ: {str(e)}")

    
    def send_quiz_poll(self, bot, chat_id, question):
        try:
            # open_peroid = get_user_config(user_id, "quiz_period")
            poll = bot.send_poll(
                chat_id=chat_id,
                question=str(question.question)[:300],
                options=[str(opt) for opt in question.options if opt],
                type="quiz",
                correct_option_id=int(question.correct_index) if question.correct_index is not None else 0,
                explanation=str(question.explanation or "")[:200],
                is_anonymous=False
                
            )

            self.poll_map[poll.poll.id] = chat_id

            return poll.message_id

        except Exception:
            import logging
            logging.exception("SEND POLL FAILED")
            return None



quiz_manager = QuizManager()

