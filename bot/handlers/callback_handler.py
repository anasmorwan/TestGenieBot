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
from bot.keyboards.account_status_keyboard import account_status_keyboard
from bot.keyboards.more_options_keyboard import more_options_keyboard
from bot.keyboards.get_chat_keyboard import get_chat_request_keyboard
from storage.quiz_repository import update_user_current_quiz, send_quiz_to_chat
from bot.bot.handlers.chat_shared_handler import publish_interactive_link



from services.usage import get_subscription_full, get_usage, build_status_message, activate_subscription, is_paid_user_active, downgrade_to_free
from services.referral import get_referral_count
from services.backup_service import safe_backup, backup_all
import random


def register(bot):

    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("pub_"))
    def handle_publishing_options(call):
        try:
            # 1. تفكيك البيانات من الـ callback_data
            # التنسيق المتوقع: pub_type_quizcode_chatid
            parts = call.data.split(":")
            if len(parts) < 3:
                bot.answer_callback_query(call.id, "⚠️ بيانات غير مكتملة.")
                return

            action_type = parts[1]      # native أو link
            quiz_code = parts[2]        # رمز الكويز
            target_chat_id = parts[3]   # آي دي القناة/المجموعة (قد يكون سالباً)

            # تحويل target_chat_id إلى رقم صحيح (Integer)
            target_chat_id = int(target_chat_id)
    
            # 2. إبلاغ المستخدم أن العمل جارٍ
            bot.answer_callback_query(call.id, "⌛ جاري النشر...")

            if action_type == "native":
                # --- خيار الاستطلاعات المباشرة (Native Polls) ---
                # استدعاء الدالة التي ترسل الأسئلة كـ Polls متتالية
                success = send_quiz_to_chat(bot, target_chat_id, quiz_code, is_pro=True)
                if success:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="✅ تم نشر الاختبار كـ **استطلاعات مباشرة** في القناة بنجاح!"
                    )
                else:
                    bot.send_message(call.message.chat.id, "❌ فشل استرجاع بيانات الاختبار.")

            elif action_type == "link":
                # --- خيار الرابط التفاعلي (Interactive Link) ---
                # النشر باستخدام الدالة المنسقة (بدون علامة مائية للمشتركين)
                success = publish_interactive_link(
                    bot, 
                    target_chat_id, 
                    quiz_code, 
                    call.from_user.first_name, 
                    watermark=False # لأنه مشترك Pro
                )
                if success:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="✅ تم نشر الاختبار كـ **رابط تفاعلي** بنجاح!"
                    )

            # 3. تسجيل عملية المشاركة في قاعدة البيانات
            log_quiz_share(quiz_code, call.from_user.id, call.from_user.first_name)

        except Exception as e:
            print(f"❌ Error in publishing callback: {e}")
            bot.answer_callback_query(call.id, "❌ فشل النشر. تأكد من صلاحيات البوت.")



    

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        try:

            data = call.data
            chat_id = call.message.chat.id
            user_id = call.from_user.id
            message_id = call.message.message_id
            print("callback:", data, flush=True)


            if data == "how_it_works":
                bot.answer_callback_query(call.id)
                keyboard = how_it_works_keyboard()
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("HOW_IT_WORKS"), reply_markup=keyboard, parse_mode="HTML")


            # استخراج quiz_code فقط إذا كان موجود
            quiz_code = None
            if ":" in data:
                quiz_code = data.split(":")[1]

            if data.startswith("start_quiz"):
                parts = data.split(":")
                quiz_code = parts[1] if len(parts) > 1 else None
                result = quiz_manager.start_quiz(chat_id, quiz_code, bot)
                print("START QUIZ RESULT:", result)

            
            elif data.startswith("post_quiz"):
                parts = data.split(":")
                quiz_code = parts[1] if len(parts) > 1 else None
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
                activate_subscription(user_id, "pro_plus")
                backup_all()
                bot.answer_callback_query(call.id)
                bot.send_message(chat_id, "📄 أرسل نص الآن لإنشاء الاختبار")

            elif data == "copylink":
                bot_username = "testprog123bot"
    
                # تصحيح القيم
                print(f"bot_username: {bot_username}")
                print(f"user_id: {user_id}")
    
                # جلب النص قبل التنسيق
                raw_text = MESSAGES["ar"]["REFERRAL_LINK"]
                print(f"Raw text: {raw_text}")
    
                # تطبيق التنسيق يدوياً للتأكد
                formatted_text = raw_text.format(username=bot_username, uid=user_id)
                print(f"Formatted text: {formatted_text}")
    
                # استخدام الدالة
                message_text = get_message("REFERRAL_LINK", username=bot_username, uid=user_id)
    
                bot.edit_message_text(
                    chat_id=chat_id, 
                    message_id=message_id, 
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

                keyboard = account_status_keyboard(user_id)

                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                        )
            
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

            elif data == "plans":
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
                    prices = [LabeledPrice(label="Pro Plan", amount=500)]
                    payload = "pro_plan"

                elif plan == "pro_plus_plan":
                    prices = [LabeledPrice(label="Pro+ Plan", amount=700)]
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

