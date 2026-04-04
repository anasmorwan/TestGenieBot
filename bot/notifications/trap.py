from bot.bot_instance import mybot
from services.user_trap import should_show_daily, update_progress
from storage.sqlite_db import get_connection
from storage.session_store import user_streak
from datetime import timedelta, datetime, date
from bot.keyboards.actions_keyboard import streak_keyboard


def send_streak():
    text = "
    user_ids = get_all_user_ids(cursor)
    for user_id in user_ids:  
        try:
            mybot.send_message(chat_id=user_id, text="🔥 تحدي اليوم جاهز!")
                
        except Exception as e:
            print(f"خطأ في إرسال تحدي اليوم:\n\n {e}")
        





def send_daily_engagement(user_id):
    keyboard = streak_keyboard()

    if should_show_daily(user_id):
        send_intial_message()
        
    user_streak[user_id] = date.today()



                

def get_all_user_ids():
    conn = get_connection
    cursor = conn.cursor()
  
    try:
        cursor.execute("SELECT user_id FROM users")
        results = cursor.fetchall()
        return [row[0] for row in results]
    except Exception as e:
        print(f"خطأ في استرجاع user_ids: {e}")
        return []
