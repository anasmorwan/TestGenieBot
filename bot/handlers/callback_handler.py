# bot/handlers/callback_handler.py
from telebot.types import LabeledPrice
from services.quiz_session_service import quiz_manager
from storage.session_store import user_states
from bot.keyboards.account_keyboard import account_keyboard
from storage.messages import get_message
from bot.keyboards.upgrade_keyboard import upgrade_keyboard
from bot.handlers.menu import send_main_menu
from bot.keyboards.upgrade_options import upgrade_options_keyboard
from bot.keyboards.pay_local import local_upgrade_options_keyboard
from bot.keyboards.premium_info_keyboard import premium_info_keyboard
from bot.keyboards.plans_keyboard import paid_plans_keyboard
from bot.keyboards.how_it_works_keyboard import how_it_works_keyboard
from bot.keyboards.referral_keyboard import referral_keyboard
from bot.keyboards.account_status_keyboard import account_status_keyboard, plan_update_keyboard_pro
from bot.keyboards.more_options_keyboard import more_options_keyboard
from bot.keyboards.get_chat_keyboard import get_chat_request_keyboard
from bot.keyboards.upsell_keyboard import saved_quiz_upsell
from storage.quiz_repository import update_user_current_quiz, send_quiz_to_chat, log_quiz_share, is_quiz_expired
from bot.handlers.chat_shared_handler import publish_interactive_link
from bot.keyboards.constumize_quiz_keyboard import get_testgenie_keyboard
from services.quiz_session_service import quiz_manager
from services.user_trap import generate_challenge
from services.usage import get_subscription_full, can_generate, get_usage, build_status_message, activate_subscription, is_paid_user_active, downgrade_to_free
from services.referral import get_referral_count
from services.backup_service import safe_backup, backup_all
from storage.session_store import user_selections, user_states
from storage.sqlite_db import get_question_distribution, get_recent_mistakes, init_user_quiz_count, update_user_difficulty
from services.user_trap import update_last_active 
from storage.session_store import user_states, temp_texts
from services.poll_service import generate_poll, normalize_poll
from bot.keyboards.actions_keyboard import send_poll_keyboard
from ‎services.referral import reward_referral_if_needed
from bot.keyboards.referral_keyboard import referral_keyboard
from bot.keyboards.customized_poll import get_poll_customize_keyboard
from bot.keyboards.get_chat_keyboard import get_chat_request_keyboard
import random
import json
import time



def register(bot):‎
    def show_referral_message(bot, chat_id, user_id):
        keyboard = referral_keyboard(user_id)
        bot.send_message(
            chat_id=chat_id, 
            text=get_message("REFERRAL_1"),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    @bot.callback_query_handler(
        func=lambda call: any([
            call.data.startswith("post_poll:"),
            call.data.startswith("regenerate:"),
            call.data == "customize_poll"
            
        ])
    )
    def handle_polls(call: CallbackQuery):
        
        chat_id = call.message.chat.id
        data = call.data
        user_id = call.from_user.id
        message_id = call.message.message_id 
        update_last_active(user_id)
        
        
        # معالجة اختيار المستوى
        if data.startswith("post_poll"):
            parts = data.split(":")
            poll_code = parts[1]
            keyboard = get_chat_request_keyboard()
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=get_message("POST_POLL"),
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            user_states[user_id] = f"post_poll:{poll_code}"
            
            temp_texts.pop(user_id, None)
            
        elif data.startswith("regenerate"):   
            try:
                allowed, info = can_generate(user_id)

                if not allowed:
                    show_referral_message(bot, chat_id, user_id)
                    return
                consume_quiz(user_id)
                reward_referral_if_needed(user_id)
                
                parts = data.split(":")
                text = parts[1]
                new_poll, poll_code = generate_poll(user_id, text, channel_name=None)
            
                action_keyboard = send_poll_keyboard(user_id, poll_code) 
                normalized = normalize_poll(new_poll)

                if not normalized:
                    raise ValueError(f"Invalid poll structure: {new_poll}")

                q_text = normalized["question"]
                q_options = normalized["options"]
                    
                bot.delete_message(chat_id, message_id)

                bot.send_poll(
                    chat_id=chat_id,
                    question=str(q_text)[:300],
                    options=[str(opt) for opt in q_options if opt],
                    type="regular",
                    is_anonymous=False
                )
                
                bot.send_message(chat_id, share_msg, reply_markup=action_keyboard, parse_mode="HTML")
                
            
            except Exception as e:
                print("File handler ERROR:", e, flush=True)
                bot.send_message(chat_id, f"❌ Error: {str(e)}")

        elif data.startswith("customize_poll"):
            parts = data.split(":")
            text = parts[1]
            # text = temp_texts.get(user_id)
            #selected_tone="ودي", selected_goal="رأي")
            keyboard = get_poll_customize_keyboard()
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=get_message("POST_POLL"),
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            pass

    @bot.callback_query_handler(
        func=lambda call: any([
            call.data.startswith("level_"),
            call.data.startswith("count_"),
            call.data == "start_test"
        ])
    )
    def handle_testgenie_callbacks(call: CallbackQuery):


        chat_id = call.message.chat.id
        data = call.data
        user_id = call.from_user.id
        update_last_active(user_id)
    
        # تهيئة بيانات المستخدم إذا لم تكن موجودة
        if chat_id not in user_selections:
            user_selections[chat_id] = {'level': 'متوسط', 'count': 10}
    
        # معالجة اختيار المستوى
        if data.startswith("level_"):
            selected_level = data.split("_")[1]
            selected_level_clean = selected_level.replace("🔒", "").strip()
            # شرط: المستوى يجب أن يكون واحداً من ['متقدم', 'متوسط', 'مبتدئ']
            # قاموس الترجمة من التسمية الظاهرة إلى القيمة المخزنة
            LEVEL_MAPPING = {
                'مبتدئ': 'early',
                'متوسط': 'mid', 
                'متقدم': 'advanced'
            }
            difficulty = LEVEL_MAPPING.get(selected_level, 'early')

            # عند معالجة اختيار المستخدم
            if selected_level_clean == "متقدم":
                if not is_paid_user_active(user_id):
                    bot.answer_callback_query(call.id, "🔓 المستوى المتقدم للمشتركين فقط")
                    return
                    
            if selected_level in ['متوسط', 'مبتدئ', 'متقدم']:
                user_selections[chat_id]['level'] = selected_level
                     
            
            
            if update_user_difficulty(user_id, difficulty):
                # تحديث لوحة المفاتيح
                new_markup = get_testgenie_keyboard(
                    user_id=user_id,
                    selected_level=selected_level,
                    selected_count=user_selections[chat_id]['count']
                )
                bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=new_markup)
                bot.answer_callback_query(call.id, f"تم اختيار المستوى: {selected_level}")
                print(f"LEVEL RAW: '{selected_level}'", flush=True)
    
        # معالجة اختيار عدد الأسئلة
        elif data.startswith("count_"):
            count_value = data.split("_")[1]
        
            # شرط: العدد يجب أن يكون 5 أو 10 أو 15 للأزرار العادية
            if count_value.isdigit() and int(count_value) in [5, 10, 15]:
                selected_count = int(count_value)
                user_selections[chat_id]['count'] = selected_count
                if init_user_quiz_count(user_id, selected_count):
                
                    new_markup = get_testgenie_keyboard(
                        user_id=user_id,
                        selected_level=user_selections[chat_id]['level'],
                        selected_count=selected_count
                    )
                    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=new_markup)
                    bot.answer_callback_query(call.id, f"تم اختيار {selected_count} سؤال")
        
            # شرط: زر مخصص (Custom)
            elif count_value == "custom":
                if not is_paid_user_active(user_id):
                    bot.answer_callback_query(call.id, "✨ أرسل عدد أسئلة من [1 — 15]")
                    user_states[user_id] = count_value
                    # يمكنك هنا إرسال رسالة تطلب من المستخدم إدخال رقم
                else:
                    bot.answer_callback_query(call.id, "✨ أرسل عدد أسئلة من [1 — 20]")
                    user_states[user_id] = count_value
        
            # شط: زر Pro (20 سؤال)
            elif count_value == "pro":
                if not is_paid_user_active(user_id):
                    bot.answer_callback_query(call.id, "🔓 20 سؤال للمشتركين فقط - قم بالترقية الآن!")
                    return
                selected_count = 20
                user_selections[chat_id]['count'] = selected_count
                if init_user_quiz_count(user_id, 20):
                    new_markup = get_testgenie_keyboard(
                        user_id=user_id,
                        selected_level=user_selections[chat_id]['level'],
                        selected_count=selected_count
                    )
                    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=new_markup)
                    bot.answer_callback_query(call.id, f"✅ تمت إختيار {selected_count} سؤال")
                    
    
        # معالجة زر بدء الاختبار
        elif data == "start_test":
            level = user_selections[chat_id]['level']
            count = user_selections[chat_id]['count']
            if level == "متقدم" and not is_paid_user_active(user_id):
                bot.answer_callback_query(call.id, "🔓 المستوى المتقدم للمشتركين فقط", show_alert=True)
                return

            if count == 20 and not is_paid_user_active(user_id):
                bot.answer_callback_query(call.id, "🔓 20 سؤال للمشتركين فقط", show_alert=True)
                return
        
            # شرط: التأكد من وجود مستوى وعدد صالحين قبل البدء
            if level and count:
                bot.answer_callback_query(call.id, f"✅ تم تحديث الإعدادات بنجاح: {count} سؤال | (مستوى {level})")
                if user_states.get(user_id) == "set_configs":
                    pass
                else:
                    new_markup = get_testgenie_keyboard(
                        user_id=user_id,
                        selected_level=level,
                        selected_count=count,
                        is_set=True
                    )
                    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=new_markup)
                
            else:
                if user_states.get(user_id) == "set_configs":
                    bot.answer_callback_query(call.id, "❌ الرجاء اختيار المستوى وعدد الأسئلة أولاً", show_alert=True)

        # معالجة أي بيانات غير متوقعة
        else:
            bot.answer_callback_query(call.id, "⚠️ خيار غير معروف")


    
    # الهاندلر الثاني (الذي كان مفقوداً): معالجة الضغط على أزرار Pro
    @bot.callback_query_handler(func=lambda call: call.data.startswith("pub:"))
    def handle_publishing_options(call):
        try:
            # تفكيك البيانات: pub:native:QC_123:-100456
            parts = call.data.split(":")
            action_type = parts[1]
            quiz_code = parts[2]
            target_chat_id = int(parts[3]) # تحويل ID القناة إلى رقم صحيح
            chat_type = parts[4]
            user_id = call.from_user.id
            update_last_active(user_id)
            

            bot.answer_callback_query(call.id, "⌛ جاري النشر في القناة...")

            if action_type == "native":
                success = send_quiz_to_chat(bot, target_chat_id, quiz_code, is_pro=True)
            elif action_type == "link":
                success = publish_interactive_link(bot, target_chat_id, quiz_code, call.from_user.first_name, watermark=False)

            if success:
                
                bot.answer_callback_query(call.id, f"✅ تم نشر الإختبار في {chat_type} بنجاح")

                # 3. تسجيل عملية المشاركة في قاعدة البيانات
                log_quiz_share(quiz_code, call.from_user.id, call.from_user.first_name)
            else:
                bot.answer_callback_query(call.id, f"❌ فشل النشر. تأكد أن البوت مشرف في {chat_type} ولديه صلاحية النشر.")

        except Exception as e:
            print(f"Error in callback pub: {e}")
            bot.answer_callback_query(call.id, "❌ حدث خطأ.")

   

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        try:

            data = call.data
            chat_id = call.message.chat.id
            user_id = call.from_user.id
            message_id = call.message.message_id
            print("callback:", data, flush=True)
            update_last_active(user_id)


            if data == "how_it_works":
                bot.answer_callback_query(call.id)
                keyboard = how_it_works_keyboard()
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("HOW_IT_WORKS"), reply_markup=keyboard, parse_mode="HTML")


            # استخراج quiz_code فقط إذا كان موجود
            quiz_code = None
            if ":" in data:
                quiz_code = data.split(":")[1]

            if data.startswith("start_challenge"):
                try:
                    parts = data.split(":")
                    challenge_type = parts[1] if len(parts) > 1 else None
                    total_mistakes = parts[2] if len(parts) > 1 else None

                    if challenge_type == "mistakes":
                        mistakes = get_recent_mistakes(user_id, total_mistakes)
                        quiz_manager.start_mistakes_review(chat_id, mistakes, bot, only_mistakes=True)
            
                    else:
                        distribution = get_question_distribution(user_id, total_questions=3)
                        review_count = distribution["review_count"]
                
                    
                        mistakes = get_recent_mistakes(user_id, review_count)
                    
                    
                        quiz_manager.start_challege(chat_id, mistakes, bot)
                        msgs = [
                            get_message("CHALLENGE_STARTED"),
                            get_message("CHALLENGE_STARTED1"),
                            get_message("CHALLENGE_STARTED2")
                        ]
                        text = random.choice(msgs)
                    
                        bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        parse_mode="HTML"
                        )
                        
                except Exception as e:
                    bot.send_message(chat_id, f"CALLBACK ERROR: {str(e)}")
                    print(f"CALLBACK ERROR: {str(e)}")
                
                
                
                       

            if data.startswith("start_quiz"):
                parts = data.split(":")
                quiz_code = parts[1] if len(parts) > 1 else None

                if is_quiz_expired(quiz_code):
                    bot.answer_callback_query(call.id)
                    keyboard = saved_quiz_upsell()
        
                    bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=get_message("SAVE_LIMIT"),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                    )
                    return

                result = quiz_manager.start_quiz(chat_id, quiz_code, bot)
                print("START QUIZ RESULT:", result)
            
            elif data.startswith("post_quiz"):
                parts = data.split(":")
                quiz_code = parts[1] if len(parts) > 1 else None
                
                if is_quiz_expired(quiz_code):
                    bot.answer_callback_query(call.id)
                    keyboard = saved_quiz_upsell()
        
                    bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=get_message("SAVE_LIMIT"),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                    )
                    return
                update_user_current_quiz(user_id, quiz_code)
                bot.answer_callback_query(call.id)
                
                
                keyboard = get_chat_request_keyboard()

                bot.send_message(chat_id=chat_id, 
                text="​📍 إختر القناة او المجموعة التي تريد مشاركة الإختبار إليها",
                reply_markup=keyboard)
                
                
                    

            elif data == "more_options":
                
                bot_username = "testprog123bot"
                bot.answer_callback_query(call.id)
                keyboard = more_options_keyboard(bot_username)
                bot.edit_message_text(chat_id=chat_id, 
                message_id=message_id, 
                text=get_message("MORE"), 
                reply_markup=keyboard, 
                parse_mode="HTML")
    
            elif data == "buy_subscription":
                keyboard = upgrade_options_keyboard()
                print("opening post_quiz menu", flush=True)
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("UPGRADE_2"), reply_markup=keyboard, parse_mode="HTML")

            elif data == "buy_subscription1":
                downgrade_to_free(user_id)
                keyboard = upgrade_options_keyboard()
                print("opening post_quiz menu", flush=True)
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("UPGRADE_2"), reply_markup=keyboard, parse_mode="HTML")
                user_states[user_id] = "pro_plan"

            elif data == "buy_subscription2":
                keyboard = upgrade_options_keyboard()
                print("opening post_quiz menu", flush=True)
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("UPGRADE_2"), reply_markup=keyboard, parse_mode="HTML")
                user_states[user_id] = "pro_plus_plan"


            
            elif data == "go_generate":
                user_states[user_id] = "awating_test"
                bot.answer_callback_query(call.id)
                bot.send_message(chat_id, "📄 أرسل الملف الآن لإنشاء الاختبار")

            elif data.startswith("quick_quiz"):
                quiz_manager.start_quiz(chat_id, quiz_code, bot)
                
            elif data == "input_text":
                backup_all()
                bot.answer_callback_query(call.id)
                bot.send_message(chat_id, "📄 أرسل نص الآن لإنشاء الاختبار")

            elif data == "copylink":
                bot_username = "testprog123bot"
    
                # تصحيح القيم
                print(f"bot_username: {bot_username}")
                print(f"user_id: {user_id}")
    
                # استخدام الدالة
                message_text = get_message("REFERRAL_LINK", username=bot_username, uid=user_id)
    
                bot.send_message(
                    chat_id=chat_id, 
                    text=message_text, 
                    parse_mode="HTML"
                )

            elif data == "go_account_settings":
                status = "free"
                print("opening account menu", flush=True)
                keyboard = account_keyboard()

                

                bot.answer_callback_query(call.id)
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("ACCOUNT_STATUS", account_status=status), reply_markup=keyboard, parse_mode="HTML"
                )

            elif data == "check_account_status":
                user_id = call.from_user.id
                chat_id = call.message.chat.id
                message_id = call.message.message_id
                bot.answer_callback_query(call.id)

                sub = get_subscription_full(user_id)
                used = get_usage(user_id)
                referrals = get_referral_count(user_id)

                message = build_status_message({
                    "user_id": user_id,   # ✅ هذا هو الحل
                    "plan": sub["plan"],
                    "used": used,
                    "limit": sub["daily_quiz_limit"],
                    "expires_at": sub["expires_at"],
                    "referrals": referrals
                })
                if is_paid_user_active(user_id):
                    keyboard = plan_update_keyboard_pro(user_id)
                else:
                    keyboard = account_status_keyboard(user_id)

                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                        )


            elif data == "update_account_status":
                from datetime import datetime
                now = datetime.utcnow().strftime("%H:%M:%S")
                
        
                user_id = call.from_user.id
                chat_id = call.message.chat.id
                message_id = call.message.message_id
                bot.answer_callback_query(call.id)

                sub = get_subscription_full(user_id)
                used = get_usage(user_id)
                referrals = get_referral_count(user_id)

                message = build_status_message({
                    "user_id": user_id,   # ✅ هذا هو الحل
                    "plan": sub["plan"],
                    "used": used,
                    "limit": sub["daily_quiz_limit"],
                    "expires_at": sub["expires_at"],
                    "referrals": referrals
                })
                message += f"\n\n⏱ آخر تحديث: {now}"

                if is_paid_user_active(user_id):
                    keyboard = plan_update_keyboard_pro(user_id)
                else:
                    keyboard = account_status_keyboard(user_id)


                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=message,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    if "message is not modified" in str(e):
                        pass
                    else:
                        raise e
            
            elif data == "upgrade_account":
                
                message_key = "UPGRADE_MAIN" if random.random() < 0.5 else "UPGRADE_BACKUP_1"
                
                bot.answer_callback_query(call.id)
                keyboard = upgrade_keyboard()
                bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=get_message(message_key),
                reply_markup=keyboard,
                parse_mode="HTML"
                )
                
            
                    
                
            elif data == "main_menu":
                send_main_menu(chat_id, message_id)

            elif data.startswith("plans"):  # ✅ startswith
                
                parts = data.split(":", maxsplit=1)
                if len(parts) > 1 and parts[1] != "":
                    pram = parts[1]
                    if pram == "tracking":
                        keyboard = paid_plans_keyboard()
                        bot.answer_callback_query(call.id)
                        bot.send_message(
                            chat_id=chat_id,
                            text=get_message("PLANS"),
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                        return

                keyboard = paid_plans_keyboard()
                bot.answer_callback_query(call.id)
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=get_message("PLANS"),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )


            plan = user_states.get(user_id)

            if data == "pay_stars" and plan:
                titles = {
                    "pro_plan": "🚀 اشتراك Pro جاهز للتفعيل",
                    "pro_plus_plan": "⚡ اشتراك Pro+ (أسرع تجربة)"
                }

                descriptions = {
                    "pro_plan": "احصل الآن على 25 اختبار يومياً + AI Vision وسرعة أعلى. التفعيل فوري بعد الدفع.",
    
                    "pro_plus_plan": "أفضل أداء ممكن: 50 اختبار يومياً + أولوية قصوى. التفعيل يتم فوراً بعد الدفع."
                }
    
                if plan == "pro_plan":
                    prices = [LabeledPrice(label="Pro Plan", amount=400)]
                    payload = "pro_plan"

                elif plan == "pro_plus_plan":
                    prices = [LabeledPrice(label="Pro+ Plan", amount=500)]
                    payload = "pro_plus_plan"

                bot.send_invoice(
                    chat_id=chat_id,
                    title=titles.get(plan, "Upgrade to Premium"),
                    description=descriptions.get(plan, "Subscribe to our premium plans"),
                    invoice_payload=payload,
                    provider_token="",
                    currency="XTR",
                    prices=prices,
                    start_parameter="upgrade"
                )
                
            elif data == "pay_local":
                bot.answer_callback_query(call.id)
                keyboard = local_upgrade_options_keyboard()
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("PAY_LOCAL"), reply_markup=keyboard, parse_mode="HTML")


            elif data == "premium_info":
                bot.answer_callback_query(call.id)
                keyboard = premium_info_keyboard()
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=get_message("PREMIUM_INFO"),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                

                

            
        except Exception as e:
            print("CALLBACK ERROR:", e, flush=True)

