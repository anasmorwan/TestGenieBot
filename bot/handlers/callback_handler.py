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

def register(bot):

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        try:

            data = call.data
            chat_id = call.message.chat.id
            user_id = call.from_user.id
            message_id = call.message.message_id
            print("callback:", data, flush=True)


            # استخراج quiz_code فقط إذا كان موجود
            quiz_code = None
            if ":" in data:
                quiz_code = data.split(":")[1]

            if data.startswith("start_quiz"):
                quiz_manager.start_quiz(chat_id, quiz_code, bot)

            elif data == "buy_subscription":
                keyboard = upgrade_options_keyboard()
                print("opening post_quiz menu", flush=True)
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("UPGRADE_2"), reply_markup=keyboard, parse_mode="HTML")
                
            elif data == "go_generate":
                user_states[user_id] = "awating_test"
                bot.answer_callback_query(call.id)
                bot.send_message(chat_id, "📄 أرسل الملف الآن لإنشاء الاختبار")

            elif data.startswith("quick_quiz"):
                quiz_manager.start_quiz(chat_id, quiz_code, bot)

            elif data == "go_account_settings":
                status = "free"
                print("opening account menu", flush=True)
                keyboard = account_keyboard()

                

                bot.answer_callback_query(call.id)
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("ACCOUNT_STATUS", account_status=status), reply_markup=keyboard, parse_mode="HTML"
                )
            
            elif data == "upgrade_account":
                bot.answer_callback_query(call.id)
                keyboard = upgrade_keyboard()
                bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=get_message("UPGRADE_MAIN"),
                reply_markup=keyboard,
                parse_mode="HTML"
                )
            elif data == "post_quiz":
                bot.answer_callback_query(call.id)
                keyboard = upgrade_keyboard()
                 
                # إرسال الرسالة
                bot.send_message(chat_id=chat_id, text=get_message("UPGRADE_1"), reply_markup=keyboard, parse_mode="HTML")
                
            elif data == "main_menu":
                send_main_menu(chat_id, message_id)


            elif data == "pay_stars":

                prices = [LabeledPrice(label="الاشتراك المميز", amount=250)]

         
                bot.send_invoice(
                    chat_id=chat_id,
                    title="تطوير الحساب (Premium)",
                    description="احصل على ميزات غير محدودة في إنشاء الاختبارات",
                    invoice_payload="user_premium_subscription",
                    provider_token="",
                    currency="XTR",
                    prices=prices,
                    start_parameter="premium-upgrade"
                )
                
            elif data == "pay_local":
                keyboard = local_upgrade_options_keyboard()
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("PAY_LOCAL"), reply_markup=keyboard, parse_mode="Markdown")

                

            
        except Exception as e:
            print("CALLBACK ERROR:", e, flush=True)

