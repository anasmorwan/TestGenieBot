from services.content_parser import save_file
from bot.bot_instance import bot
from services.content_parser import is_file_size_allowed

def handle_file_upload(msg):

    uid = msg.from_user.id
    chat_id = msg.chat.id
    file_id = msg.document.file_id
    file_name = msg.document.file_name

    if not is_file_size_allowed(bot, file_id):
        bot.send_message(chat_id, "الملف كبير جداً (الحد 5MB)")
        return

    file_info = bot.get_file(file_id)
    
    try:
        file_data = bot.download_file(file_info.file_path)
    except Exception as e:
        print("Download error:", e)
        bot.send_message(chat_id, "لم أستطع قراءة الملف.")
        return

    path = save_file(uid, file_name, file_data)

    return path
