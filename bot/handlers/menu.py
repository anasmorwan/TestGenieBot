# menu.py
# تم النقل
from storage.sqlite_db import is_user_exist, log_new_user

from bot.bot_instance import mybot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.main_menu import main_menu_keyboard

def send_main_menu(chat_id, message_id=None):
    bot_username = mybot.get_me().username
    keyboard = main_menu_keyboard(bot_username)
    text = (
        "*👋 مرحباً بك في TestGenie*"
        "\n\n"
        "حوّل ملفاتك إلى اختبارات تفاعلية خلال 10 ثوانٍ.\n\n"
        "📄 أرسل:\n"
        "PDF • DOCX • نص\n\n"
        "وسيحوّله البوت إلى اختبار تلقائياً.\n\n"
        "👇 أو اختر:"
    )

    if message_id:
        mybot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        mybot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
