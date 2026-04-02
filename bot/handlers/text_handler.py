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
from storage.session_store import user_states, get_state_safe, get_chat_title
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

            # 👇 فقط إذا مسموح
            consume_quiz(user_id)
            # backup_all()
            # 👇 تحقق هل هذا مستخدم جديد تمت دعوته
            reward_referral_if_needed(user_id)
            # backup_all()

        except Exception as e:
            print("File handler ERROR:", e, flush=True)
            bot.send_message(chat_id, f"❌ Error: {str(e)}") 


        if not text.strip():
            bot.send_message(chat_id, "⚠️ الرجاء إرسال نص لتوليد الاختبار.")
            return



        
        try:
            state = get_state_safe(user_id)
            
            if state == "awaiting_poll_text":
                if has_previous_poll(user_id):
                    group_selection = get_message("POLL_TO_CHAT")
          
                
                    if len(text) < 200:
                        keybord = get_chat_request_keyboard()    
                        bot.send_message(chat_id, group_selection, reply_markup=keyboard, parse_mode="HTML")
                        user_states[user_id] = "poll"
                        return
                        
                    else:
                        #error_text = get_message("REGECTED_POLL_TXT")
                        # cancel_keyboard = escape_action_keyboard()  
                        # bot.send_message(chat_id, error_text, parse_mode="HTML", reply_markup=cancel_keyboard)
                        #time.sleep(2)
                        # action_keybord = get_chat_request_keyboard()
                        
                        keyboard = get_chat_request_keyboard()    
                        bot.send_message(chat_id, group_selection, reply_markup=keyboard, parse_mode="HTML")
                    
                        user_states[user_id] = "poll"
                        return
                        

                else:
                    
                    user_states[user_id] = "generate_poll"
          
                    
                    
                    
                    

            elif state == "generate_poll":
                chat_title = get_chat_title(user_id)
                share_msg = get_message("POST_POLL_TEXT")
                text = get_message("GENERATE_POLL")
                
                bot.send_message(chat_id, text, parse_mode="HTML")
                
                
                poll_code, poll = generate_poll(user_id, text, channel_name=chat_title)
                action_keyboard = send_poll_keyboard(text, poll_code)
                
                bot.send_poll(
                        chat_id=chat_id,
                        question=str(poll.question)[:300],
                        options=[str(opt) for opt in poll.options if opt],
                        type="regular",
                        explanation=str(question.explanation or "")[:200],
                        is_anonymous=False
                )
                bot.send_message(chat_id, share_msg, reply_markup=action_keybord, parse_mode="HTML")
                return
                
                


            else:
            
                waiting_msg = bot.send_message(chat_id, get_message("Generating quiz"))
                # توليد الأسئلة
                quizzes = generate_quizzes_from_text(text, user_id)

                if not quizzes or len(quizzes) == 0:
                    bot.send_message(chat_id, "❌ فشل توليد الاختبار. تأكد أن النص يحتوي على معلومات كافية.")
                    return

                # تخزين الاختبار
                quiz_code = store_quiz(user_id, quizzes)
                maybe_cleanup()
                # backup_all()
                quiz_len = len(quizzes)


                bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=waiting_msg.message_id,
                        text=get_message("QUIZ_CREATED", count=quiz_len),
                        reply_markup=quiz_keyboard(quiz_c
                                                ode),
                        parse_mode="HTML"
                    )
            
        except Exception as e:
            print("File handler ERROR:", e, flush=True)
            bot.send_message(chat_id, f"❌ Error: {str(e)}")
    
