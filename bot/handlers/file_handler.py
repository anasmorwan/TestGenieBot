from utils.content_parser import parse_file_content
from services.quiz_service import generate_quizzes_from_text
from storage.quiz_repository import store_quiz
from services.quiz_session_service import quiz_manager


def register(bot):

    @bot.message_handler(content_types=["document"])
    def handle_file_upload(msg):

        # 1 استخراج النص
        content = parse_file_content(bot, msg)

        if not content:
            bot.send_message(msg.chat.id, "لم أستطع قراءة الملف.")
            return

        # 2 توليد الأسئلة
        quizzes = generate_quizzes_from_text(content, msg.from_user.id)

        if not quizzes:
            bot.send_message(msg.chat.id, "فشل توليد الاختبار.")
            return

        # 3 تخزين الاختبار
        quiz_code = store_quiz(msg.from_user.id, quizzes)

        # 4 بدء الاختبار
        quiz_manager.start_quiz(msg.chat.id, quiz_code, bot)
