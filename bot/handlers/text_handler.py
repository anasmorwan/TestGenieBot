from services.quiz_service import generate_quizzes_from_text
from storage.quiz_repository import store_quiz
from services.quiz_session_service import quiz_manager
from storage.messages import get_message
from services.referral import show_referral_message, reward_referral_if_needed
from services.usage import consume_quiz, can_generate
from bot.keyboards.referral_keyboard import referral_keyboard



def register(bot):

    def show_referral_message(bot, chat_id):
        keyboard = referral_keyboard()
        bot.send_message(
        chat_id=chat_id, 
        text=get_mesaage("REFFERAL_1"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    @bot.message_handler(content_types=["text"])
    def handle_text_message(msg):
        user_id = msg.from_user.id
        chat_id = msg.chat.id
        text = msg.text


        allowed, reason = can_generate(user_id)


        
        if not allowed:
            if reason == "limit_reached":
                show_referral_message(bot, chat_id)

        # 👇 استهلك محاولة
        consume_quiz(user_id)
        # 👇 تحقق هل هذا مستخدم جديد تمت دعوته
        reward_referral_if_needed(user_id)


        if not text.strip():
            bot.send_message(chat_id, "⚠️ الرجاء إرسال نص لتوليد الاختبار.")
            return
            
        waiting_msg = bot.send_message(chat_id, get_message("Generating quiz"))
        # توليد الأسئلة
        quizzes = generate_quizzes_from_text(text, user_id)

        if not quizzes or len(quizzes) == 0:
            bot.send_message(chat_id, "❌ فشل توليد الاختبار. تأكد أن النص يحتوي على معلومات كافية.")
            return

        # تخزين الاختبار
        quiz_code = store_quiz(user_id, quizzes)

        # بدء الاختبار مباشرة
        quiz_manager.start_quiz(chat_id, quiz_code, bot)

    
