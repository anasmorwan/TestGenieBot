from bot.bot_instance import mybot
from services.user_trap import should_show_daily, update_progress
from storage.sqlite_db import get_connection
from storage.session_store import user_streak
from datetime import timedelta, datetime, date
from bot.keyboards.actions_keyboard import streak_keyboard


def send_streak(user_id, streak, xp):
    keyboard = streak_keyboard()
    text = f"🔥 <b>تحدي اليوم جاهز!</b>\n\n💡 هل يمكنك الحفاظ على سلسلة 🔥 <b>{streak}</b> أيام؟\n\nابدأ الآن واختبر نفسك 👇"
    
    # user_ids = get_all_user_ids(cursor)   
    try:
        mybot.send_message(chat_id=user_id, text=text, reply_markup=keyboard, parse_mode="HTML")
                
    except Exception as e:
        print(f"خطأ في إرسال تحدي اليوم:\n\n {e}")
        





def send_daily_engagement():
    user_ids = [5048253124, 6948343253]
    for user_id in user_ids:
        
        if should_show_daily(user_id):
            streak, xp = update_progress(user_id)
            send_streak(user_id, streak, xp)
        
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
