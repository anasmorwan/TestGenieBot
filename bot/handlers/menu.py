# menu.py
# تم النقل
from storage.sqlite_db import is_user_exist, get_today_attempts, get_normal_questions_total, log_new_user, get_user_mistakes_stats
from storage.messages import get_message
from services.user_trap import update_last_active

from bot.bot_instance import mybot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.main_menu import main_menu_keyboard, smart_ui_keyboard


def send_main_menu(chat_id, message_id=None):
    

    bot_username = mybot.get_me().username
    
    base_text = get_message("BASE_TEXT")
    ux_text = get_message("UX_TEXT")
    
    mistakes_stat = get_user_mistakes_stats(chat_id)
    total_mistakes = mistakes_stat.get("total_mistakes")
    recent_mistakes = mistakes_stat.get("recent_mistakes")
    total_questions = get_normal_questions_total(chat_id)
    todays_attempts = get_today_attempts(chat_id)
    todays_score = None
    if todays_attempts:
        todays_score = todays_attempts[0]["correct_answers"]
    else:
        print("لا توجد محاولات لهذا اليوم")
    #return {
       # "total_mistakes": total_mistakes,
     #   "recent_mistakes": recent_mistakes,
     #   "avg_fail_count": round(avg_fail, 2)
 #   }
    
    new_text = get_message("MAIN_MENU", total_today=todays_score, mistakes_count=total_mistakes)
    
    # النص المتغير (التحية أو مقدمة مخصصة)
    welcome_new_user = "<b>👋 مرحباً بك في Qube</b>\n\n"
    welcome_returning_user = "<b>أهلاً بك، أنا Qube.. كيف يمكنني أن أختبر ذكاءك اليوم؟\n\n"

    
    if is_user_exist(chat_id):
        text = new_text
        keyboard = smart_ui_keyboard(recent_mistakes)
        parse_mode = "HTML"
        

    else:    
        text = ux_text
        keyboard = None
        parse_mode = "HTML"
    
    
    if message_id:
        
        text = new_text
        smart_ui_keyboard(recent_mistakes)
        # keyboard = main_menu_keyboard(bot_username)
        
        mybot.edit_message_text(
            text=text,
            chat_id=chat_id,
            reply_markup=keyboard,
            message_id=message_id,
            parse_mode=parse_mode
        )
    else:
        text = ux_text
        mybot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )


#attempts = []
#    for row in results:
 # attempt = {
 #           'id': row[0],
      #      'user_id': row[1],
      #      'correct_answers': row[2],
     #       'total_questions': row[3],
 #           'quiz_type': row[4],
   #         'created_at': row[5]
   #     }
