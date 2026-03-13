from utils.content_parser import extract_text_from_file
from services.quiz_service import generate_quizzes_from_text
from storage.quiz_repository import store_quiz
from services.quiz_session_service import quiz_manager
from bot_instance import bot

def register(bot):

    @bot.message_handler(content_types=["document"])
    def handle_file_upload(msg):
        user_id = msg.from_user.id
        chat_id = msg.chat.id
        message_id = msg.message.id

        # 1 استخراج النص
        content = extract_text_from_file(user_id, bot, msg, path, chat_id, message_id)
        if not content:
            bot.send_message(chat_id, "لم أستطع قراءة الملف.")
            return

        # 1b استخراج user_instruction من caption إذا وجد
        user_instruction = getattr(msg, "caption", None)
        if user_instruction:
            user_instruction = user_instruction.strip()

        # 2 توليد الأسئلة مع تمرير التعليمات (اختياري)
        quizzes = generate_quizzes_from_text(
            content=content,
            user_id=user_id,
            user_instruction=user_instruction
        )

        if not quizzes:
            bot.send_message(chat_id, "فشل توليد الاختبار.")
            return

        # 3 تخزين الاختبار
        quiz_code = store_quiz(user_id, quizzes)

        # 4 بدء الاختبار
        quiz_manager.start_quiz(chat_id, quiz_code, bot)
