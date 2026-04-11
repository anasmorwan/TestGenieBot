# menu.py
# تم النقل
from storage.sqlite_db import is_user_exist, calculate_daily_review_limit, get_today_attempts, get_normal_questions_total, log_new_user, get_user_mistakes_stats
from storage.messages import get_message
from services.user_trap import update_last_active

from bot.bot_instance import mybot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.main_menu import main_menu_keyboard, smart_ui_keyboard


def send_main_menu(chat_id, message_id=None):

    bot_username = mybot.get_me().username
      

    
    limit = calculate_daily_review_limit(chat_id) 
    mistakes_stat = get_user_mistakes_stats(chat_id)

    
    total_mistakes = mistakes_stat.get("total_mistakes") 
    
    total_questions = get_normal_questions_total(chat_id)
    todays_attempts = get_today_attempts(chat_id)
    todays_questions = 0
    if todays_attempts:
        todays_questions = todays_attempts[0]["total_questions"]
    else:
        print("لا توجد محاولات لهذا اليوم")

    
    smart_ui_text = get_message("MAIN_MENU", total_today=todays_questions, mistakes_count=total_mistakes)
    base_text = get_message("BASE_TEXT")
    ux_text = get_message("UX_TEXT")
    

    if total_mistakes == 0:
        smart_ui_text = get_message("MENU_NO_MISTAKES")
    

    text = ux_text
    keyboard = None
    parse_mode = "HTML"

    
    if is_user_exist(chat_id):
        text = smart_ui_text
        keyboard = smart_ui_keyboard(limit)
        
    
    if message_id:
        text = smart_ui_text
        keyboard = smart_ui_keyboard(limit)
        
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
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
