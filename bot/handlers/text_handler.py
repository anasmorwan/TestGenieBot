from services.quiz_service import generate_quizzes_from_text
from storage.quiz_repository import store_quiz
from services.quiz_session_service import quiz_manager

def register(bot):
    
    @bot.message_handler(content_types=["text"])
    def handle_text_message(msg):
        user_id = msg.from_user.id
        chat_id = msg.chat.id
        text = msg.text

        if not text.strip():
            bot.send_message(chat_id, "⚠️ الرجاء إرسال نص لتوليد الاختبار.")
            return
            
        waiting_msg = bot.send_message(chat_id, "Generating quiz…")
        # توليد الأسئلة
        quizzes = generate_quizzes_from_text(text, user_id)

        if not quizzes or len(quizzes) == 0:
            bot.send_message(chat_id, "❌ فشل توليد الاختبار. تأكد أن النص يحتوي على معلومات كافية.")
            return

        # تخزين الاختبار
        quiz_code = store_quiz(user_id, quizzes)

        # بدء الاختبار مباشرة
        quiz_manager.start_quiz(chat_id, quiz_code, bot)

    

    # الخطوة 2: ماذا يحدث بعد نجاح الدفع؟
    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        # هنا يمكنك تحديث قاعدة البيانات للمستخدم
        # message.successful_payment.invoice_payload سيعطيك "user_premium_subscription"
        bot.send_message(message.chat.id, "شكراً لك! تم تفعيل الاشتراك بنجاح 🌟")
