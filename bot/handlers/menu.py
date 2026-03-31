# menu.py
# تم النقل
from storage.sqlite_db import is_user_exist, log_new_user
from storage.messages import get_message


from bot.bot_instance import mybot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.main_menu import main_menu_keyboard

def send_main_menu(chat_id, message_id=None):
    

    bot_username = mybot.get_me().username
    
    base_text = get_message("BASE_TEXT")
    ux_text = get_message("UX_TEXT")
    
    # النص المتغير (التحية أو مقدمة مخصصة)
    welcome_new_user = "*👋 مرحباً بك في TestGenie*\n\nحوّل ملفاتك إلى اختبارات تفاعلية خلال 10 ثوانٍ.\n\n"
    welcome_returning_user = "*👋 مرحباً بك مجددًا في TestGenie*\n\nما الذي ترغب في القيام به اليوم؟\n\n"

    
    if is_user_exist(chat_id):
        text = ux_text
        
        keyboard = None
        parse_mode = "HTML"
        

    else:    
        text = ux_text
        keyboard = None
        parse_mode = "HTML"
    
    
    if message_id:
        
        text = welcome_new_user + base_text
        keyboard = main_menu_keyboard(bot_username)
        
        mybot.edit_message_text(
            text=text,
            chat_id=chat_id,
            reply_markup=keyboard,
            message_id=message_id,
            parse_mode=parse_mode
        )
    else:
        mybot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )

