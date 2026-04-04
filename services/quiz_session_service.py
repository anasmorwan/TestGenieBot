import sqlite3
from storage.sqlite_db import get_connection
import json
from datetime import datetime
from models.quiz import QuizQuestion
# from services.poll_service import send_quiz_poll
import threading
from services.usage import is_paid_user_active
from storage.messages import get_message
from bot.keyboards.upsell_keyboard import quiz_number_limit_upsell, tracking_upsell_keyboard
from storage.quiz_attempts import log_quiz_attempt, get_quiz_stats, build_quiz_viral_message, get_quiz_creator, format_usernames, get_quiz_user_ids
from analytics.shared_quiz_analytics import get_hardest_question, get_success_rate, build_advanced_stats_message
from bot.keyboards.quiz_buttons import share_quiz_button
from services.usage import is_paid_user_active
import random
import time



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

    def start_mistakes_review(self, chat_id, questions, bot):
        # هذه دالة جديدة تبدأ اختباراً من الأخطاء فقط
        with self.lock:
            self.sessions[chat_id] = {
                "questions": questions,
                "index": 0,
                "score": 0,
                "source": "mistakes_pool", # 👈 هنا نضع العلامة
                "quiz_code": "REVIEW_MODE"
            }
        self.send_current_question(chat_id, bot)
    

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

        
    def save_mistake(self, user_id, q_obj):
        conn = get_connection()
        c = conn.cursor()
    
        options_json = json.dumps(q_obj.options)
    
        # التحقق من وجود السؤال
        c.execute("""
            SELECT id, fail_count FROM user_mistakes 
            WHERE user_id = ? AND question_text = ?
        """, (user_id, q_obj.question))
    
        existing = c.fetchone()
    
        if existing:
            # تحديث الخطأ الموجود
            c.execute("""
                UPDATE user_mistakes 
                SET options = ?, correct_index = ?, explanation = ?, 
                   last_failed = ?, fail_count = fail_count + 1
                WHERE user_id = ? AND question_text = ?
            """, (options_json, q_obj.correct_index, q_obj.explanation, 
                  datetime.now().isoformat(), user_id, q_obj.question))
        else:
            # إدراج خطأ جديد مع created_at
            c.execute("""
                INSERT INTO user_mistakes 
                (user_id, question_text, options, correct_index, explanation, 
                 last_failed, created_at, fail_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (user_id, q_obj.question, options_json, q_obj.correct_index, 
                  q_obj.explanation, datetime.now().isoformat(), datetime.now().isoformat()))
    
        conn.commit()
        conn.close()

    
    def increment_correct_count(self, user_id, question_text):
        conn = get_connection()
        c = conn.cursor()
    
        # زيادة العداد
        c.execute("""
            UPDATE user_mistakes 
            SET correct_count = correct_count + 1 
            WHERE user_id = ? AND question_text = ?
        """, (user_id, question_text))
    
        # حذف الأسئلة التي أتقنها المستخدم (أجاب عليها صح مرتين مثلاً)
        c.execute("DELETE FROM user_mistakes WHERE correct_count >= 2")
    
        conn.commit()
        conn.close()

    
    def reset_correct_count(self, user_id, question_text):
        """إعادة تعيين عداد الإتقان للصفر لأن المستخدم أخطأ في السؤال مجدداً"""
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("""
                UPDATE user_mistakes 
                SET correct_count = 0, 
                   last_failed = ? 
                WHERE user_id = ? AND question_text = ?
            """, (datetime.now().isoformat(), user_id, str(question_text)))
            conn.commit()
        except Exception as e:
            print(f"❌ Error resetting count: {e}")
        finally:
            conn.close()
        
    
    
    

    def handle_answer(self, chat_id, selected_option, bot, is_shared_user=None):
        state = self.sessions.get(chat_id)
        if not state:
            return

        # إذا لم يُمرر is_shared_user كمعامل، نقرأه من الجلسة
        shared = state.get("is_shared_user") if is_shared_user is None else is_shared_user

        q = state["questions"][state["index"]]

        if state.get("source") == "mistakes_pool":   
            if is_correct:
                # إذا أجاب صح على سؤال كان خطأ سابقاً، نزيد عداد الإتقان
                self.increment_correct_count(chat_id, q.question)
            else:
                # إذا أخطأ فيه مجدداً، نعيد تصفير العداد لضمان بقائه في التدريب
                self.reset_correct_count(chat_id, q.question)
        else:
            # إذا كان اختباراً عادياً (ليس مراجعة) وأخطأ المستخدم
            if not is_correct:
                self.save_mistake(chat_id, q)
            

        if selected_option == q.correct_index:
            state["score"] += 1

        state["index"] += 1

        if state["index"] >= len(state["questions"]):
            
            self.finish_quiz(chat_id, bot, is_shared_user=shared)

        
        else:
            self.send_current_question(chat_id, bot)






    
    def finish_quiz(self, chat_id, bot, is_shared_user=None):
    
        state = self.sessions.pop(chat_id, None)
        if not state:
            return

        # ✅ استخراج جميع البيانات مرة واحدة في البداية
        score = state.get("score", 0)
        total = len(state["questions"])
        quiz_code = state.get("quiz_code")   
        shared = is_shared_user if is_shared_user is not None else state.get("is_shared_user")
        text = f"انتهى الاختبار\n\nالنتيجة: {score}/{total}"


        
        if not is_paid_user_active(chat_id) and not shared:
            extra_quiz_msg = get_message("QUIZ_LIMIT")
            if extra_quiz_msg:
                text += f"\n\n{extra_quiz_msg}"

            keyboard = share_quiz_button(quiz_code)
            try:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                print(f"✅ تم إرسال النتيجة للمستخدم {chat_id}")          
            except Exception as e:
                print(f"❌ فشل إرسال النتيجة: {e}")
                bot.send_message(chat_id, f"خطأ: {str(e)}")


        
        elif is_paid_user_active(chat_id) and not shared:
            extra_quiz_msg = get_message("QUIZ_LIMIT")
            if extra_quiz_msg:
                text += f"\n\n{extra_quiz_msg}"
            keyboard = share_quiz_button(quiz_code)
            
            try:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                print(f"✅ تم إرسال النتيجة للمستخدم {chat_id}")           
            except Exception as e:
                print(f"❌ فشل إرسال النتيجة: {e}")
                bot.send_message(chat_id, f"خطأ: {str(e)}")

        
        elif shared:
            try:
                if quiz_code:
                    creator_id = get_quiz_creator(quiz_code)
                    log_quiz_attempt(chat_id, quiz_code, score, total)            
            except Exception as e:
                print(f"❌ فشل إرسال التقرير: {e}")
                bot.send_message(chat_id, f"خطأ: {str(e)}")


            

    def send_quiz_poll(self, bot, chat_id, q):
        try:
            # 1. الوصول للبيانات عبر الكائن (Object Attributes) وليس القاموس
            # نستخدم getattr كإجراء أمان إضافي أو الوصول المباشر
            q_text = getattr(q, 'question', 'سؤال بدون عنوان')
            options = getattr(q, 'options', [])
            correct_idx = getattr(q, 'correct_index', 0)
            explanation_text = getattr(q, 'explanation', '')

            # 2. الحماية: قص النصوص لتطابق قيود تيليجرام (300 للسؤال، 100 للخيار، 200 للشرح)
            safe_question = str(q_text)[:300]
        
            # التأكد من أن كل خيار لا يتجاوز 100 حرف (حل خطأ 400 السابق)
            safe_options = [str(opt)[:100] for opt in options if opt]
        
            # الشرح بحد أقصى 200 حرف
            safe_explanation = str(explanation_text)[:200]

            # 3. إرسال الـ Poll
            poll = bot.send_poll(
                chat_id=chat_id,
                question=safe_question,
                options=safe_options,
                type="quiz",
                correct_option_id=int(correct_idx) if correct_idx is not None else 0,
                explanation=safe_explanation,
                is_anonymous=False
            )

            self.poll_map[poll.poll.id] = chat_id
            return poll.message_id

        except Exception as e:
            import logging
            logging.error(f"SEND POLL FAILED for chat {chat_id}: {e}")
            return None
    



quiz_manager = QuizManager()


