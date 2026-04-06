from bot.bot_instance import mybot
from services.user_trap import should_show_daily, update_progress, get_user_content, is_inactive
from storage.sqlite_db import get_connection
from storage.session_store import user_streak
from datetime import timedelta, datetime, date
from bot.keyboards.actions_keyboard import streak_keyboard
import threading
from services.quiz_service import generate_challenge_quiz
from services.usage import is_paid_user_active




def send_daily_challenge_message():
    user_ids = [5048253124, 6948343253]
    for user_id in user_ids:
        
        if is_inactive(user_id):
            streak, xp = update_progress(user_id)
            keyboard = streak_keyboard()
            
            text = f"🔥 <b>تحدي اليوم جاهز!</b>\n\n💡 هل يمكنك الحفاظ على سلسلة 🔥 <b>{streak}</b> أيام؟\n\nابدأ الآن واختبر نفسك 👇"
            try:
                mybot.send_message(chat_id=user_id, text=text, reply_markup=keyboard, parse_mode="HTML")
                
            except Exception as e:
                print(f"خطأ في إرسال تحدي اليوم:\n\n {e}")
        
        
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
