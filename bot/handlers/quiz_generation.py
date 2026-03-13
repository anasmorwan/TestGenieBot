from services.content_parser import save_file, extract_text_from_file
from services.quiz_service import generate_quizzes_from_text
from bot.bot_instance import bot


def handle_file_upload(msg):

    uid = msg.from_user.id
    chat_id = msg.chat.id

    file_name = msg.document.file_name
    file_id = msg.document.file_id

    file_info = bot.get_file(file_id)
    file_data = bot.download_file(file_info.file_path)

    path = save_file(uid, file_name, file_data)

    content = extract_text_from_file(path)

    quizzes = generate_quizzes_from_text(content, uid)

    bot.send_message(chat_id, f"تم توليد {len(quizzes)} سؤال!")
