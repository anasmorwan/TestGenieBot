import random
import time
import sqlite3
import json
import threading
from datetime import datetime


from models.quiz import QuizQuestion
from storage.sqlite_db import get_connection, save_quiz_attempt, get_user_major, get_user_difficulty, user_has_quizzes, get_question_distribution



from services.usage import is_paid_user_active, can_generate, get_current_pro_quota
from storage.messages import get_message
from bot.keyboards.upsell_keyboard import quiz_number_limit_upsell, tracking_upsell_keyboard
from storage.quiz_attempts import log_quiz_attempt, get_quiz_stats, build_quiz_viral_message, get_quiz_creator, format_usernames, get_quiz_user_ids
from analytics.shared_quiz_analytics import get_hardest_question, get_success_rate, build_advanced_stats_message
from bot.keyboards.quiz_buttons import share_quiz_button, too_mistakes_keyboard, few_mistakes_keyboard, pro_quota_keyboard
from services.usage import is_paid_user_active
from services.user_trap import generate_challenge, update_progress, get_weakness_line, get_feedback_line, build_result_message, get_user_content
from services.quiz_service import normalize_quizzes





admin_id = 5048253124

class QuizManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        
        # ✅ هذا هو الناقص
        self.poll_map = {}

    def generate_and_store(self, bot=None, chat_id=None, user_id=None, message_id=None, only_generate=False):
        try:
            print(f"🚀 [START] Starting generation for user_id: {user_id}", flush=True)

            distribution = get_question_distribution(user_id, total_questions=3)
            challenge_count = distribution["challenge_count"]
            new_count = distribution["new_count"]

            print(f"📊 [INFO] Distribution: {new_count} new, {challenge_count} challenge.", flush=True)

            should_resume = False
            state = None

            if user_id is not None:
                print(f"📡 [API] Requesting quizzes from AI...", flush=True)
                raw_quizzes = generate_challenge(bot, user_id, new_count, challenge_count)
                quizzes = normalize_quizzes(raw_quizzes)
                print(f"✅ [API] Received {len(quizzes)} quizzes.", flush=True)

                with self.lock:
                    state = self.sessions.get(chat_id)
                    if not state:
                        return

                    current_count = len(state["questions"])
                    was_waiting = state.get("waiting_for_extension", False)
                    current_index = state["index"]

                    state["questions"].extend(quizzes)
                    state["is_extended"] = True
                    state["waiting_for_extension"] = False

                    should_resume = was_waiting and current_index >= current_count


                    state["questions_resumed"] = True

            if should_resume:
                if message_id:
                    bot.delete_message(chat_id, message_id=message_id)
                    time.sleep(1)
                    
                                          
                print(f"▶️{should_resume} [RESUME] Resuming quiz for chat_id: {chat_id}", flush=True)
                

                self.send_current_question(chat_id, bot)

                with self.lock:
                    if state:
                        state["questions_resumed"] = True

            print(f"🏁 [FINISH] generate_and_store completed successfully.", flush=True)

        except Exception as e:
            print(f"❌ [ERROR] Error in generate_and_store: {str(e)}", flush=True)
            raise ValueError(f"generate_and_store_error: {str(e)}")
        

    def start_quiz(self, chat_id, quiz_code, bot, is_shared_user=None):
        try:
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
                    "source": "generated_quiz",
                    "extended": False,
                    "quiz_code": quiz_code,
                    "wrong_count": 0,
                    "is_shared_user": is_shared_user   # ✅ أضف هذا السطر
                }
        
        
            self.send_current_question(chat_id, bot, is_shared_user=None)
    

            return True
        except Exception as e:
            raise ValueError(f"start_quizError: {str(e)}")
            

    def start_challege(self, chat_id, mistakes_list, bot):
        try:
            questions = []
            if mistakes_list:
                for mistake in mistakes_list:
                    q_data = mistake.get("questions") if isinstance(mistake, dict) else None
                    if q_data:
                        obj = QuizQuestion.from_raw(q_data)
                        if obj: questions.append(obj)
            
            # التحقق من وجود مادة علمية هنا أولاً
            user_content = get_user_content(chat_id)
            has_content = user_content is not None

            with self.lock:
                self.sessions[chat_id] = {
                    "questions": questions,
                    "index": 0,
                    "score": 0,
                    "wrong_count": 0,
                    "source": "dynamic_mix",
                    "quiz_code": "CHALLENGE_MODE",
                    "has_saved_texts": has_content, # 👈 ستكون True أو False بدقة
                    "is_extended": False,
                    "waiting_for_extension": True,
                    "questions_resumed": False
                }

            if questions:
                self.send_current_question(chat_id, bot)
                if has_content:
                    threading.Thread(target=self.generate_and_store, args=(bot, chat_id, chat_id)).start()
            else:
                if has_content:
                    bot.send_message(chat_id, "🔍 جاري توليد أسئلة تحدي جديدة بناءً على تخصصك...")
                    threading.Thread(target=self.generate_and_store, args=(bot, chat_id, chat_id)).start()
                else:
                    bot.send_message(chat_id, "⚠️ لا توجد أخطاء سابقة، ولم تقم بإضافة نصوص أو ملفات لتوليد أسئلة جديدة. يرجى إرسال نص أولاً!")
                    with self.lock:
                        self.sessions.pop(chat_id, None)

        except Exception as e:
            print(f"❌ Error in start_mistakes_review: {str(e)}")

    def start_user_review(self, chat_id, bot):
        try:
    
            content = get_user_content(user_id)
            if content is None:
                bot send_message(
                chat_id,
                text=get_message("NO_QUIZ_TEXT"),
                parse_mode="HTML"
                )
                return
            waitinf_msg = bot send_message(
                chat_id,
                text=get_message("USER_REVIEW"),
                parse_mode="HTML"
            )
            with self.lock:
                timestamp = int(time.time()) 
                quiz_code = f"{chat_id}_{timestamp}"
                self.sessions[chat_id] = {
                    "questions": [],
                    "index": 0,
                    "score": 0,
                    "wrong_count": 0,
                    "source": "user_review",
                    "quiz_code": quiz_code,
                    "has_saved_texts": True,
                    "is_extended": False,
                    "waiting_for_extension": False,
                    "questions_resumed": False
                }
            threading.Thread(target=self.generate_and_store, args=(bot, chat_id, chat_id)).start()
    

    def start_mistakes_review(self, chat_id, mistakes_list, bot, only_mistakes=False):
        try:
            questions = []
            if mistakes_list:
                for mistake in mistakes_list:
                    q_data = mistake.get("questions") if isinstance(mistake, dict) else None
                    if q_data:
                        obj = QuizQuestion.from_raw(q_data)
                        if obj: questions.append(obj)
            
            # التحقق من وجود مادة علمية هنا أولاً
            user_content = get_user_content(chat_id)
            has_content = user_content is not None

            with self.lock:
                self.sessions[chat_id] = {
                    "questions": questions,
                    "index": 0,
                    "score": 0,
                    "wrong_count": 0,
                    "source": "mistakes",
                    "quiz_code": "CHALLENGE_MODE",
                    "has_saved_texts": has_content, # 👈 ستكون True أو False بدقة
                    "is_extended": False,
                    "waiting_for_extension": False,
                    "questions_resumed": False
                }

            if questions:
                self.send_current_question(chat_id, bot, only_mistakes)
                
            else:
                text = random.choice([get_message("NO_QUIZ_TEXT"), get_message("NO_MISTAKES")])
                bot.send_message(chat_id, text=text, parse_mode="HTML")
                with self.lock:
                    self.sessions.pop(chat_id, None)

        except Exception as e:
            print(f"❌ Error in start_mistakes_review: {str(e)}")
                                     


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
    

    def send_current_question(self, chat_id, bot, is_shared_user=None, only_mistakes=False):
        trap_msg = "⏱ لا تفكر كثيراً… أجب بسرعة"
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

        self.send_quiz_poll(bot, chat_id, q, only_mistakes)

        
    def save_mistake(self, user_id, q_obj):
        conn = get_connection()
        c = conn.cursor()

        options_json = json.dumps(q_obj.options)
    
        # 🔴 التحقق من الحد الأقصى للمستخدم المجاني
        if not is_paid_user_active(user_id):
            # حساب عدد الأخطاء الحالية
            c.execute("""
                SELECT COUNT(*) FROM user_mistakes 
                WHERE user_id = ?
            """, (user_id,))
        
            mistake_count = c.fetchone()[0]
        
            # إذا وصل للحد الأقصى (10)، لا تحفظ الخطأ الجديد
            if mistake_count >= 10:
                conn.close()
                return False  # لم يتم الحفظ

        # التحقق من وجود السؤال
        c.execute("""
            SELECT id, fail_count, correct_count FROM user_mistakes 
            WHERE user_id = ? AND question_text = ?
        """, (user_id, q_obj.question))

        existing = c.fetchone()

        if existing:
            # ✅ تحديث الخطأ الموجود: زيادة fail_count وإعادة تعيين correct_count
            c.execute("""
                UPDATE user_mistakes 
                SET options = ?, 
                    correct_index = ?, 
                    explanation = ?, 
                    last_failed = ?, 
                    branch = ?,
                    fail_count = fail_count + 1,
                    correct_count = 0
                WHERE user_id = ? AND question_text = ?
            """, (options_json, q_obj.correct_index, q_obj.explanation, 
                  datetime.now().isoformat(), q_obj.branch, user_id, q_obj.question))
        else:
            # ✅ إدراج خطأ جديد
            c.execute("""
                INSERT INTO user_mistakes 
                (user_id, question_text, options, correct_index, explanation, 
                 last_failed, created_at, branch, fail_count, correct_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            """, (user_id, q_obj.question, options_json, q_obj.correct_index, 
                    q_obj.explanation, datetime.now().isoformat(), datetime.now().isoformat(), q_obj.branch))

        conn.commit()
        conn.close()
        return True

    
    def increment_correct_count(self, user_id, question_text):
        conn = get_connection()
        c = conn.cursor()
    
        # زيادة العداد أولاً
        c.execute("""
            UPDATE user_mistakes 
            SET correct_count = correct_count + 1 
            WHERE user_id = ? AND question_text = ?
        """, (user_id, question_text))
    
        # حذف الأسئلة التي أتقنها المستخدم (أجاب عليها صح مرتين)
        c.execute("""
            DELETE FROM user_mistakes 
            WHERE user_id = ? AND correct_count >= 2
        """, (user_id,))
    
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
        
    
    
    def handle_answer(self, chat_id, selected_option, bot, is_shared_user=None, only_mistakes=False):
        try:
            with self.lock:
                state = self.sessions.get(chat_id)
                if not state:
                    return

                shared = state.get("is_shared_user") if is_shared_user is None else is_shared_user
                source = state.get("source")

                q = state["questions"][state["index"]]
                is_correct = (selected_option == q.correct_index)
                

                if is_correct:
                    state["score"] += 1
                    if source != "mistakes":
                        update_progress(chat_id, correct=1, total=None)
                    if state.get("source") == "dynamic_mix":
                        try:
                            self.increment_correct_count(chat_id, q.question)
                        except Exception as db_e:
                            print(f"⚠️ تجاهل خطأ قاعدة البيانات (increment): {db_e}")
                else:
                    state["wrong_count"] += 1
                    
                    if source not in ("dynamic_mix", "mistakes"):
                        try:
                            self.save_mistake(chat_id, q)
                        except Exception as db_e:
                            print(f"⚠️ تجاهل خطأ قاعدة البيانات (save_mistake): {db_e}")
                    else:
                        try:
                            self.reset_correct_count(chat_id, q.question)
                        except Exception as db_e:
                            print(f"⚠️ تجاهل خطأ قاعدة البيانات (reset): {db_e}")

                state["index"] += 1

                if state["index"] >= len(state["questions"]):
                    waiting_for_extension = state.get("waiting_for_extension")
               # else:
                #    state["waiting_for_extension"]

            if state["index"] >= len(state["questions"]) and source == "dynamic_mix":
                
                distribution = get_question_distribution(chat_id, total_questions=3)
                challenge_count = distribution["challenge_count"]
                new_count = distribution["new_count"]
                mistakes = distribution["review_count"]
                update = -mistakes
                update_progress(chat_id, correct=update, total=None)
                    
                if waiting_for_extension:
                    
                    text = random.choice([get_message("WAITING_CHAL_QUIZ_1", new_count=new_count, challenge_count=challenge_count), get_message("WAITING_CHAL_QUIZ")])
                    waiting_msg = bot.edit_message_text(
                        chat_id,
                        message_id=message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    with self.lock:
                        state.get("questions_resumed")
                    if questions_resumed:
                        generate_and_store(message_id=waiting_msg.message_id)
                    return

                self.finish_quiz(chat_id, bot, shared, only_mistakes)
                print("⚡ finishing quiz.", flush=True)
                return

            self.send_current_question(chat_id, bot)

        except Exception as e:
            print(f"❌ CRITICAL ERROR in handle_answer: {e}")
            import traceback
            traceback.print_exc()



        
    
    def finish_quiz(self, chat_id, bot, is_shared_user=None, only_mistakes=False):
        print("entered finish quiz...", flush=True)
    
        state = self.sessions.pop(chat_id, None)
        if not state:
            return

        # --------------------------
        #          Values
        # --------------------------
        score = state.get("score", 0)
        total = len(state["questions"])
        quiz_code = state.get("quiz_code")
        wrong = state.get("wrong_count", 0)
        shared = is_shared_user if is_shared_user is not None else state.get("is_shared_user")
        feedback_line = get_feedback_line(score, total)
        streak, xp = update_progress(chat_id)
        weakness_line = get_weakness_line(chat_id, wrong)
        prepared_text = build_result_message(chat_id, score, total, streak, xp)
        has_text = state.get("has_saved_texts")
        source = state.get("source")
        self.poll_map.pop(chat_id, None)
        wrongs_ratio = wrong / total
        user_major = get_user_major(chat_id)
        
        # --------------------------------
        #          Logics
        # --------------------------------
        # 1\ save quiz totals for user [for usage in the main menu]
        save_quiz_attempt(chat_id, score, total)
    
        if not is_paid_user_active(chat_id) and not shared:
            is_allowed, info = can_generate(chat_id)
            remaining_pro = get_current_pro_quota(chat_id)
            remaining = info.get("remaining")
            has_quizzes = user_has_quizzes(chat_id)
            
            if source == "dynamic_mix" and not has_text:
                bot.send_message(chat_id, text=get_message("NO_QUIZ_TEXT"), parse_mode="HTML")
                return

            elif is_allowed and remaining == 2 and not has_quizzes: 
                keyboard = pro_quota_keyboard()
                text = random.choice([get_message("QUOTA_OFFER_1", total=total, score=score), get_message("QUOTA_OFFER_2", total=total, score=score)])
                bot.send_message(
                    chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                return
                
            elif source == "generated_quiz" or has_text:
                
                # keyboard = share_quiz_button(quiz_code)
                keyboard = None
                try:
                    if source == "mistakes":
                        with self.lock:
                            wrong = state.get("wrong_count", 0)
                            total = len(state.get("questions"))
                            wrongs_ratio = wrong / total

                    
                    if wrongs_ratio <= 0.4:
                        keyboard = too_mistakes_keyboard(wrong)
                    else:
                        keyboard = few_mistakes_keyboard(wrong)
                    bot.send_message(
                        chat_id=chat_id,
                        text=build_result_message(chat_id, score, total, streak, xp),
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    print(f"✅ تم إرسال النتيجة للمستخدم {chat_id}")          
                except Exception as e:
                    print(f"❌ فشل إرسال النتيجة: {e}")
                    bot.send_message(chat_id, f"خطأ: {str(e)}")

        
        
        elif is_paid_user_active(chat_id) and not shared:
            extra_quiz_msg = get_message("QUIZ_LIMIT")
            if source == "dynamic_mix":
                if not has_text:
                    bot.send_message(chat_id, text=get_message("NO_QUIZ_TEXT"), parse_mode="HTML")
                    return
                
            
            if source == "generated_quiz" or has_text:
                keyboard = share_quiz_button(quiz_code)
                if wrongs_ratio <= 0.4:
                    keyboard = too_mistakes_keyboard(wrong)
                else:
                    keyboard = few_mistakes_keyboard(wrong)
                    
            
                try:
                    bot.send_message(
                        chat_id=chat_id,
                        text=get_message("TRAP_MSG", total=total, score=score, xp=xp, streak=streak, feedback_line=feedback_line, weakness_line=weakness_line),
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    print(f"✅ تم إرسال النتيجة للمستخدم {chat_id}")           
                except Exception as e:
                    print(f"❌ فشل إرسال النتيجة: {e}")
                    bot.send_message(chat_id, f"خطأ: {str(e)}")

        
        elif shared:
            if quiz_code:
                creator_id = get_quiz_creator(quiz_code)
                log_quiz_attempt(chat_id, quiz_code, score, total)
                
            if source == "dynamic_mix":
                if not has_text:
                    bot.send_message(chat_id, text=get_message("NO_QUIZ_TEXT"), parse_mode="HTML")
                    return
                
            if source == "generated_quiz" or has_text:
                try:
                    keyboard = share_quiz_button(quiz_code)
                    if wrongs_ratio <= 0.4:
                        keyboard = too_mistakes_keyboard(wrong)
                    else:
                        keyboard = few_mistakes_keyboard(wrong)
                    
                    bot.send_message(
                        chat_id=chat_id,
                        text=get_message("TRAP_MSG", total=total, xp=xp, score=score, streak=streak, feedback_line=feedback_line, weakness_line=weakness_line),
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"❌ فشل إرسال التقرير: {e}")
                    bot.send_message(chat_id, f"خطأ: {str(e)}")


            

    def send_quiz_poll(self, bot, chat_id, q, only_mistakes=False):
        try:
            
            # 1. الوصول للبيانات عبر الكائن (Object Attributes) وليس القاموس
            # نستخدم getattr كإجراء أمان إضافي أو الوصول المباشر
            state = self.sessions.get(chat_id)
            questions = state.get("questions")
            
            q_text = getattr(q, 'question', 'سؤال بدون عنوان')
            options = getattr(q, 'options', [])
            correct_idx = getattr(q, 'correct_index', 0)
            explanation_text = getattr(q, 'explanation', '')
            branch = getattr(q, 'branch', '')
            current_index = state.get("index")
            total = len(questions)
            user_difficlty = get_user_difficulty(chat_id)

            
            header = f"{current_index + 1}/{total} •\n\n"
            if user_difficlty == "early":
                header = f"{current_index + 1}/{total} • {branch}\n\n"
                

            # 2. الحماية: قص النصوص لتطابق قيود تيليجرام (300 للسؤال، 100 للخيار، 200 للشرح)
            safe_question = header + str(q_text)[:285]
            safe_options = [str(opt)[:100] for opt in options if opt is not None]
                 
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
            

            with self.lock:
                self.poll_map[poll.poll.id] = {
                    "chat_id": chat_id,
                    "only_mistakes": only_mistakes
                }
            return poll.message_id

        except Exception as e:
            import logging
            logging.error(f"SEND POLL FAILED for chat {chat_id}: {e}")
            return None
    



quiz_manager = QuizManager()



