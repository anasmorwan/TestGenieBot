import os

MAX_FILE_SIZE = 5 * 1024 * 1024


def is_file_size_allowed(bot, file_id):

    file_info = bot.get_file(file_id)
    return file_info.file_size <= MAX_FILE_SIZE


def save_file(uid, file_name, file_data):

    os.makedirs("downloads", exist_ok=True)

    path = os.path.join("downloads", file_name)

    with open(path, "wb") as f:
        f.write(file_data)

    return path


def is_text_empty(text):

    return not text.strip()


def extract_text_from_file(path):

    # هنا منطق قراءة PDF / TXT
    with open(path, "r", encoding="utf8") as f:
        return f.read()
