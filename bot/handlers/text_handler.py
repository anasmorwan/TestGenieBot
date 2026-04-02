from services.quiz_service import generate_quizzes_from_text
from storage.quiz_repository import store_quiz, maybe_cleanup, has_previous_poll
from services.quiz_session_service import quiz_manager
from storage.messages import get_message
from services.referral import reward_referral_if_needed
from services.usage import consume_quiz, can_generate, check_subscription_valid
from bot.keyboards.referral_keyboard import referral_keyboard
from services.backup_service import safe_backup, backup_all
from services.backup_service import smart_restore, is_db_valid
from bot.keyboards.quiz_buttons import quiz_keyboard
from storage.session_store import user_states, get_state_safe, get_chat_title, temp_texts
from bot.keyboards.actions_keyboard import send_poll_keyboard, escape_action_keyboard
from services.poll_service import generate_poll
from bot.keyboards.get_chat_keyboard import get_chat_request_keyboard

def register(bot):

    def show_referral_message(bot, chat_id, user_id):
        keyboard = referral_keyboard(user_id)
        bot.send_message(
            chat_id=chat_id, 
            text=get_message("REFERRAL_1"),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    @bot.message_handler(func=lambda msg: msg.chat.type == "private", content_types=["text"])
    def handle_text_message(msg):
        if msg.chat.type != "private":
            return
            
        user_id = msg.from_user.id
        chat_id = msg.chat.id
        text = msg.text

        try:
            plan = check_subscription_valid(user_id)
            allowed, info = can_generate(user_id)

            if not allowed:
                show_referral_message(bot, chat_id, user_id)
                return

            consume_quiz(user_id)
            reward_referral_if_needed(user_id)

        except Exception as e:
            print(f"Auth/Usage Error for user {user_id}: {e}", flush=True)
            bot.send_message(chat_id, f"❌ Error: {str(e)}") 
            return

        if not text.strip():
            bot.send_message(chat_id, "⚠️ الرجاء إرسال نص لتوليد الاختبار.")
            return

        try:
            state = get_state_safe(user_id)
            print(f"DEBUG: [User: {user_id}] current_state: {state}", flush=True)
            
            if state == "awaiting_poll_text":
                print(f"DEBUG: [User: {user_id}] Entered awaiting_poll_text block", flush=True)
                if has_previous_poll(user_id):
                    print(f"DEBUG: [User: {user_id}] Found previous polls. Asking for group.", flush=True)
                    group_selection = get_message("POLL_TO_CHAT")
                    keyboard = get_chat_request_keyboard()    
                    bot.send_message(chat_id, group_selection, reply_markup=keyboard, parse_mode="HTML")
                    user_states[user_id] = "poll"
                    return
                else:
                    print(f"DEBUG: [User: {user_id}] No previous polls. Moving to generate_poll state.", flush=True)
                    user_states[user_id] = "generate_poll"
                    state = "generate_poll"
                    # يمكنك إضافة رسالة توضيحية هنا إذا لزم الأمر
                    
                        
            if state == "generate_poll":
                print(f"DEBUG: [User: {user_id}] Logic: Executing generation sequence", flush=True)
                chat_title = get_chat_title(user_id)
                share_msg = get_message("POST_POLL_TEXT")
                wait_text = get_message("GENERATE_POLL")
                
                waiting_msg = bot.send_message(chat_id, wait_text, parse_mode="HTML")
                
                print(f"DEBUG: [User: {user_id}] Calling AI for Poll...", flush=True)
                poll_code, poll = generate_poll(user_id, text, channel_name=chat_title)
                
                temp_texts[user_id] = text
                
                action_keyboard = send_poll_keyboard(user_id, poll_code) 
                
                # استخراج البيانات
                q_text = poll.get('poll', 'Poll') if isinstance(poll, dict) else poll.question
                q_options = poll.get('answers', []) if isinstance(poll, dict) else poll.options
                
                bot.delete_message(chat_id, waiting_msg.message_id)

                bot.send_poll(
                    chat_id=chat_id,
                    question=str(q_text)[:300],
                    options=[str(opt) for opt in q_options if opt],
                    type="regular",
                    is_anonymous=False
                )
                
                bot.send_message(chat_id, share_msg, reply_markup=action_keyboard, parse_mode="HTML")
                user_states[user_id] = None 
                print(f"DEBUG: [User: {user_id}] generate_poll COMPLETED", flush=True)
                return

            elif state is None or state == "" or state == "idle":
                # الحالة الافتراضية توليد اختبار عادي
                print(f"DEBUG: [User: {user_id}] No specific state found. Starting standard Quiz generation.", flush=True)
                waiting_msg = bot.send_message(chat_id, get_message("Generating quiz"))
                
                quizzes = generate_quizzes_from_text(text, user_id)

                if not quizzes or len(quizzes) == 0:
                    print(f"DEBUG: [User: {user_id}] Quiz generation returned EMPTY result.", flush=True)
                    bot.send_message(chat_id, "❌ فشل توليد الاختبار. تأكد أن النص يحتوي على معلومات كافية.")
                    return

                quiz_code = store_quiz(user_id, quizzes)
                maybe_cleanup()
                quiz_len = len(quizzes)

                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=waiting_msg.message_id,
                    text=get_message("QUIZ_CREATED", count=quiz_len),
                    reply_markup=quiz_keyboard(quiz_code), 
                    parse_mode="HTML"
                )
                print(f"DEBUG: [User: {user_id}] Standard Quiz {quiz_code} generated and sent.", flush=True)
            
        except Exception as e:
            print(f"CRITICAL ERROR [User: {user_id}]: {e}", flush=True)
            bot.send_message(chat_id, f"❌ Error: {str(e)}")
            user_states.pop(user_id, None)

        finally:
            user_states.pop(user_id, None)  # None يمنع الخطأ إذا لم يكن المفتاح موجودًا



