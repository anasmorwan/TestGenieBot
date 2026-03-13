from services.content_parser import save_file, extract_text_from_file
from services.quiz_service import generate_quizzes_from_text
from bot.bot_instance import bot
from services.poll_service import send_quiz_poll


def handle_file_upload(msg):

    uid = msg.from_user.id
    chat_id = msg.chat.id

    file_id = msg.document.file_id
    file_name = msg.document.file_name

    file_info = bot.get_file(file_id)

    if file_info.file_size > MAX_FILE_SIZE:
        bot.send_message(chat_id, "الملف كبير جداً (الحد 5MB)")
        return

    file_data = bot.download_file(file_info.file_path)

    path = save_file(uid, file_name, file_data)

    content = extract_text_from_file(path)

    quizzes = generate_quizzes_from_text(content, uid)
    
    send_quiz_poll(chat_id, quizzes)

    bot.send_message(chat_id, f"تم توليد {len(quizzes)} سؤال")
