# menu.py
# تم النقل

from bot.bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.main_manu import main_menu_keyboard 

def send_main_menu(chat_id, message_id=None):
    BOT_USERNAME = bot.get_me().username
    keyboard = main_menu_keyboard
    text = (
        "👋 مرحباً بك في TestGenie\n\n"
        "حوّل ملفاتك إلى اختبارات تفاعلية خلال 10 ثوانٍ.\n\n"
        "📄 أرسل:\n"
        "PDF • DOCX • نص\n\n"
        "وسيحوّله البوت إلى اختبار تلقائياً.\n\n"
        "👇 أو اختر:"
    )

    if message_id:
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        bot.send_message(
            chat_id,
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
