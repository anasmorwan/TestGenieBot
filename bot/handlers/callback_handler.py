# bot/handlers/callback_handler.py
from telebot.types import LabeledPrice
from services.quiz_session_service import quiz_manager
from storage.session_store import user_states
from bot.keyboards.account_keyboard import account_keyboard
def register(bot):

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):

        data = call.data
        quiz_code = data.split(":")[1]
        chat_id = call.message.chat.id
        user_id = call.from_user.id


        if data.startswith("start_quiz"):
            quiz_manager.start_quiz(chat_id, quiz_code, bot)

        elif data == "post_quiz":
            # مثال: إرسال عرض لشراء ميزات إضافية بنجوم تيليغرام
            prices = [LabeledPrice(label="الاشتراك المميز", amount=250)] # 250 نجمة
            
            bot.send_invoice(
                chat_id=chat_id,
                title="تطوير الحساب (Premium)",
                description="احصل على ميزات غير محدودة في إنشاء الاختبارات",
                invoice_payload="user_premium_subscription", # معرف داخلي تطلبه لاحقاً للتأكد
                provider_token="", # اتركها فارغة لنجوم تيليغرام
                currency="XTR",    # رمز نجوم تيليغرام
                prices=prices,
                start_parameter="premium-upgrade"
            )
        elif data == "go_generate":
            user_states[user_id] = "awating_test"
            


        elif data.startswith("quick_quiz"):
            quiz_manager.start_quiz(chat_id, quiz_code, bot)

        elif data == "go_account_settings":
            keyboard = account_keyboard
            

            text = (
                "⚙️ حسابك في البوت\n\n"
                "هل تريد معرفة حالة حسابك أو فتح جميع الميزات؟\n\n"
                "مع الحساب المدفوع تحصل على:\n"
                "• اختبارات غير محدودة\n"
                "• معالجة أسرع للملفات\n"
                "• تجربة تعلم أفضل\n\n"
                "اختر ما تريد:"
                )

            
           bot.send_message(chat_id, text, reply_markup=keyboard)
