import os # لا تنسى استيراد مكتبة نظام التشغيل
from utils.content_parser import extract_text_from_file, is_file_size_allowed
from services.quiz_service import generate_quizzes_from_text
from storage.quiz_repository import store_quiz
from services.quiz_session_service import quiz_manager
from services.file_upload import handle_file_upload
# from services.poll_service import send_quiz_message
from bot.keyboards.quiz_buttons import quiz_keyboard
from storage.messages import get_message




def register(bot):

    @bot.message_handler(content_types=["document"])
    def handle_file(msg):

        user_id = msg.from_user.id
        chat_id = msg.chat.id
        message_id = msg.message.id

        path = handle_file_upload(msg)
        content = None

        try:

            if path:
                content = extract_text_from_file(
                    user_id,
                    bot,
                    msg,
                    path,
                    chat_id,
                    message_id
                )
            else:
                print("Error during file upload", flush=True)

            if not content:
                bot.send_message(chat_id, "لم أستطع قراءة الملف.")
                return

            user_instruction = getattr(msg, "caption", None)
            if user_instruction:
                user_instruction = user_instruction.strip()

            quizzes = generate_quizzes_from_text(
                content=content,
                user_id=user_id,
                user_instruction=user_instruction
            )

            if not quizzes:
                bot.send_message(chat_id, "فشل توليد الاختبار.")
                return

            quiz_code = store_quiz(user_id, quizzes)
            quiz_len = len(quizzes)

            bot.send_message(
                chat_id,
                text=get_message("QUIZ_CREATED", count=quiz_len),
                reply_markup=quiz_keyboard(quiz_code),
                parse_mode=HTML
            )

        finally:
            if path and os.path.exists(path):
                os.remove(path)
                print(f"تم حذف الملف المؤقت: {path}")
