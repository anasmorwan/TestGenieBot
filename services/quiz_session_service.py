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
        quiz_code = state.get("quiz_code")  # استخراج quiz_code
    
        # إذا لم تُمرر القيمة، نستخدم المخزنة في الجلسة (احتياطي)
        shared = is_shared_user if is_shared_user is not None else state.get("is_shared_user")

        # بناء النص الأساسي
        text = f"انتهى الاختبار\n\nالنتيجة: {score}/{total}"

        if not is_paid_user_active(chat_id) and not shared:
            extra_quiz_msg = get_message("QUIZ_LIMIT")
            if extra_quiz_msg:
                text += f"\n\n{extra_quiz_msg}"

            keyboard = share_quiz_button(quiz_code)
    
            # ✅ إرسال الرسالة وتسجيل المحاولة
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
                    stats = get_quiz_stats(quiz_code)

                    # if stats["users"] >= 3 and stats["completed"] < 5:

                
                    if stats["users"] >= 3:
                    
                        user_ids = get_quiz_user_ids(quiz_code)
                        names = format_usernames(bot, user_ids)

                        message = build_quiz_viral_message(stats, names)
                        keyboard = tracking_upsell_keyboard()
                    
                        bot.send_message(chat_id=creator_id, text=message, reply_markup=keyboard)

     
                    elif stats["users"] >= 3 and stats["completed"] >= 5:
                        hardest = get_hardest_question(quiz_code)
                        success = get_success_rate(quiz_code)
                        message = build_advanced_stats_message(stats, hardest, success)
                        keyboard = tracking_upsell_keyboard()
                        bot.send_message(chat_id=creator_id, text=message, reply_markup=keyboard)

                        waiting_msg = bot.send_message(chat_id, "⏳ جارٍ تحليل النتائج...")
                    
                        wait_time = random.uniform(1, 3)
                        time.sleep(wait_time)

                    
                        if random.randint(0, 1) == 1:  # 50% احتمال
                            bot.edit_message_text(
                                chat_id=chat_id, 
                                message_id=waiting_msg.message_id, 
                                text="🎉"
                            )
                            time.sleep(2)
                    
                        bot.edit_message_text(chat_id, message_id=waiting_msg.message_id, text=message, reply_markup=keyboard, parse_mode="HTML")
                        
            except Exception as e:
                print(f"❌ فشل إرسال التقرير: {e}")
                bot.send_message(chat_id, f"خطأ: {str(e)}")


            
"""            
    
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

"""
    def send_quiz_poll(self, bot, chat_id, question_dict):
        """
        إرسال استطلاع رأي مع حماية كاملة من قيود تيليجرام
        """
        try:
            # 1. الوصول للمفاتيح باستخدام القواميس (Dictionary Access)
            # مع استخدام .get() لتجنب KeyError
            q_text = question_dict.get('question', 'سؤال بدون عنوان')
            options = question_dict.get('options', [])
            correct_idx = question_dict.get('correct_index', 0)
            # التأكد من وجود المفتاح الجديد 'explanation'
            explanation_text = question_dict.get('explanation', '')

            # 2. الحماية: قص النصوص لتطابق قيود تيليجرام الصارمة
            # السؤال: بحد أقصى 300 حرف
            safe_question = str(q_text)[:300]
        
            # الخيارات: بحد أقصى 100 حرف لكل خيار (حل مشكلة الخطأ 400)
            safe_options = [str(opt)[:100] for opt in options if opt]
        
            # الشرح: بحد أقصى 200 حرف
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


