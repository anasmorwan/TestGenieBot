from bot.bot_instance import bot
# قائمة الملفات لكل مستخدم (تغييرها إلى dict)
user_files = {}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def is_file_size_allowed(bot, file_id):
    file_info = bot.get_file(file_id)
    return file_info.file_size <= MAX_FILE_SIZE



def save_file(uid, file_name, file_data):
    os.makedirs("downloads", exist_ok=True)
    path = os.path.join("downloads", f"{uid}_{file_name}")
    with open(path, "wb") as f:
        f.write(file_data)
    user_files[uid] = path
    return path



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
