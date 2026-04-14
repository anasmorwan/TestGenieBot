from services.quiz_service import generate_quizzes_from_text
from storage.quiz_repository import store_quiz, maybe_cleanup, has_previous_poll
from services.quiz_session_service import quiz_manager
from storage.messages import get_message
from services.referral import reward_referral_if_needed
from services.usage import consume_quiz, can_generate, check_subscription_valid
from bot.keyboards.referral_keyboard import referral_keyboard
from services.backup_service import safe_backup, backup_all
from services.backup_service import smart_restore, is_db_valid
from bot.keyboards.quiz_buttons import quiz_keyboard, scheduled_quiz_keyboard
from storage.session_store import user_states, get_state_safe, get_chat_title, temp_texts
from bot.keyboards.actions_keyboard import send_poll_keyboard, escape_action_keyboard
from services.poll_service import generate_poll, normalize_poll
from bot.keyboards.get_chat_keyboard import get_chat_request_keyboard
from services.user_trap import update_last_active
from storage.sqlite_db import set_user_has_quizzes, init_user_quiz_count
from bot.keyboards.actions_keyboard import invitation_keyboard
from bot.handlers.is_member import is_user_member, get_channel_invite_link
from services.usage import is_paid_user_active

from core.queue_manager import add_task
import time
import random

def register(bot):

    def show_referral_message(bot, chat_id, user_id):
        keyboard = referral_keyboard(user_id)
        bot.send_message(
            chat_id=chat_id, 
            text=get_message("REFERRAL_1"),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    def show_channel_invitation(bot, chat_id):
        invite_link = get_channel_invite_link(bot)
        keyboard = invitation_keyboard(invite_link)
        bot.send_message(
        chat_id=chat_id, 
        text=get_message("CHANNEL", invite_link=invite_link),
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
        update_last_active(user_id)
        if text.startswith("/"):
            return

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
                    group_selection = get_message("POST_POLL_TEXT")
                    keyboard = get_chat_request_keyboard()    
                    bot.send_message(chat_id, group_selection, reply_markup=keyboard, parse_mode="HTML")
                    user_states[user_id] = "poll"
                    temp_texts[user_id] = text
                    return
                else:
                    print(f"DEBUG: [User: {user_id}] No previous polls. Moving to generate_poll state.", flush=True)
                    user_states[user_id] = "generate_poll"
                    state = "generate_poll"
                    # يمكنك إضافة رسالة توضيحية هنا إذا لزم الأمر
                    
                        
            if state == "generate_poll":
                try:
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
                    normalized = normalize_poll(poll)

                    if not normalized:
                        raise ValueError(f"Invalid poll structure: {poll}")

                    q_text = normalized["question"]
                    q_options = normalized["options"]
                    
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
                except Exception as e:
                    bot.send_message(chat_id, f"فشل إنشاء إستطلاع.\n\n {str(e)}")
                    user_states.pop(user_id, None)
                finally:
                    user_states.pop(user_id, None)

            elif state == "custom":
                if not text.isdigit():
                    bot.send_message(chat_id, "⚠️ أرسل رقما فقط لتحديد الإختبارات")
                    return
    
                num = int(text)
                if not is_paid_user_active(user_id):
                    if not (1 <= num <= 15):
                        bot.send_message(chat_id, "✍️ متاح لك عدد إختبارات من 1-15 في خطتك")
                        return
                else:
                    if not (1 <= num <= 20):
                        bot.send_message(chat_id, "✍️ متاح لك عدد إختبارات من 1-20 في خطتك")
                        return
    
                init_user_quiz_count(user_id, num)  # فقط إذا وصلنا لهنا يعني الرقم صحيح
                user_states.pop(user_id, None)
                return

            
            

            elif state is None or state == "" or state in ["scheduled_quiz", "awaiting_schedule"]:
                
                if state == "awaiting_schedule":
                    keyboard = scheduled_quiz_keyboard()
                    bot.send_message(
                        chat_id=chat_id,
                        text=get_message("AWAITING_SCHEDULE_CONTENT"),
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    user_states[user_id] = "scheduled_quiz"
                    temp_texts[user_id] = text
                    return

                
                waiting_msg = bot.send_message(chat_id, get_message("Generating_quiz"))
                msg_id = waiting_msg.message_id

                # quizzes = generate_quizzes_from_text(text, user_id, bot, msg_id=msg_id)
                add_task(1, {
                    "type": "text_generate_quiz",
                    "user_id": user_id,
                    "text": text,
                    "msg_id": msg_id
                })

                
                
                
        except Exception as e:
            print(f"CRITICAL ERROR [User: {user_id}]: {e}", flush=True)
            bot.send_message(chat_id, f"❌ Error: {str(e)}")
            
