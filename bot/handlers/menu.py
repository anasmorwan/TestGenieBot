# menu.py
# تم النقل
from storage.sqlite_db import is_user_exist, log_new_user
from storage.messages import gey_message


from bot.bot_instance import mybot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.main_menu import main_menu_keyboard

def send_main_menu(chat_id, message_id=None):
    if message.chat.type != "private":
        
        return

    bot_username = mybot.get_me().username
    keyboard = main_menu_keyboard(bot_username)
    base_text = get_mesaage("BASE_TEXT")
    
    # النص المتغير (التحية أو مقدمة مخصصة)
    welcome_new_user = "*👋 مرحباً بك في TestGenie*\n\nحوّل ملفاتك إلى اختبارات تفاعلية خلال 10 ثوانٍ.\n\n"
    welcome_returning_user = "*👋 مرحباً بك مجددًا في TestGenie*\n\nما الذي ترغب في القيام به اليوم؟\n\n"

    if is_user_exist(chat_id):
        text = welcome_returning_user + base_text

    else:
        text = welcome_new_user + base_text
    
    
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


"""
text = (
        "*👋 مرحباً بك في TestGenie*"
        "\n\n"
        "حوّل ملفاتك إلى اختبارات تفاعلية خلال 10 ثوانٍ.\n\n"
        "📄 أرسل:\n"
        "PDF • DOCX • نص\n\n"
        "وسيحوّله البوت إلى اختبار تلقائياً.\n\n"
        "👇 أو اختر:"
    )
"""
