# bot/handlers/callback_handler.py
from telebot.types import LabeledPrice
from services.quiz_session_service import quiz_manager
from storage.session_store import user_states
from bot.keyboards.account_keyboard import account_keyboard
from storage.messages import get_message
from bot.keyboards.upgrade_keyboard import upgrade_keyboard
from bot.handlers.menu import send_main_menu
from bot.keyboards.upgrade_options import upgrade_options_keyboard


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
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=get_message("UPGRADE_2"))
                
            elif data == "go_generate":
                user_states[user_id] = "awating_test"
                bot.answer_callback_query(call.id)
                bot.send_message(chat_id, "📄 أرسل الملف الآن لإنشاء الاختبار")

            elif data.startswith("quick_quiz"):
                quiz_manager.start_quiz(chat_id, quiz_code, bot)

            elif data == "go_account_settings":
                print("opening account menu", flush=True)
                keyboard = account_keyboard()

                text = ("<b>⚙️ حسابك في TestGenie</b>\n\n"
                    "حسابك الحالي: مجاني\n\n"
                    "يمكنك:\n"
                    "• إنشاء عدد محدود من الاختبارات يومياً\n\n"
                    "<b>🚀 مع TestGenie Pro ستحصل على:</b>\n"
                    "• اختبارات بدون قيود\n"
                    "• سرعة معالجة أعلى\n"
                    "• دعم ملفات أكبر\n\n"
                    "اختر ما تريد:")

                bot.answer_callback_query(call.id)
                bot.edit_message_text(chat_id=chat_id, text=text, message_id=message_id, reply_markup=keyboard, parse_mode="HTML")

            
            elif data == "upgrade_account":
                bot.answer_callback_query(call.id)
                keyboard = upgrade_keyboard()
                 
            
                # إرسال الرسالة
                bot.send_message(chat_id, text=get_message("UPGRADE_MAIN"), reply_markup=keyboard, parse_mode="HTML")
                
            elif data == "post_quiz":
                bot.answer_callback_query(call.id)
                keyboard = upgrade_keyboard()
                 
                # إرسال الرسالة
                bot.send_message(chat_id, text=get_message("UPGRADE_1"), reply_markup=keyboard, parse_mode="HTML")
                
            elif data == "main_menu":
                send_main_menu(chat_id, message_id)


            elif data == " starts_payments":

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

                




            
        except Exception as e:
            print("CALLBACK ERROR:", e, flush=True)

