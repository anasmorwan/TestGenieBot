# bot/handlers/callback_handler.py
from telebot.types import LabeledPrice
from services.quiz_session_service import quiz_manager
from storage.session_store import user_states
from bot.keyboards.account_keyboard import account_keyboard



def register(bot):

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        try:

            data = call.data
            chat_id = call.message.chat.id
            user_id = call.from_user.id
            print("callback:", data, flush=True)


            # استخراج quiz_code فقط إذا كان موجود
            quiz_code = None
            if ":" in data:
                quiz_code = data.split(":")[1]

            if data.startswith("start_quiz"):
                quiz_manager.start_quiz(chat_id, quiz_code, bot)

            elif data == "post_quiz":
                print("opening post_quiz menu", flush=True)
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

            elif data == "go_generate":
                user_states[user_id] = "awating_test"
                bot.answer_callback_query(call.id)
                bot.send_message(chat_id, "📄 أرسل الملف الآن لإنشاء الاختبار")

            elif data.startswith("quick_quiz"):
                quiz_manager.start_quiz(chat_id, quiz_code, bot)

            elif data == "go_account_settings":
                print("opening account menu", flush=True)
                keyboard = account_keyboard()

                text = (
                    "⚙️ حسابك في البوت\n\n"
                    "هل تريد معرفة حالة حسابك أو فتح جميع الميزات؟\n\n"
                    "مع الحساب المدفوع تحصل على:\n"
                    "• اختبارات أكثر\n"
                    "• معالجة أسرع للملفات\n"
                    "• تجربة تعلم أفضل\n\n"
                    "اختر ما تريد:"
                )

                bot.answer_callback_query(call.id)
                bot.send_message(chat_id, text, reply_markup=keyboard)

            
        except Exception as e:
            print("CALLBACK ERROR:", e, flush=True)

