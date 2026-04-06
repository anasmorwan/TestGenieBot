from bot.bot_instance import mybot
from services.user_trap import should_show_daily, update_progress, get_user_content
from storage.sqlite_db import get_connection
from storage.session_store import user_streak
from datetime import timedelta, datetime, date
from bot.keyboards.actions_keyboard import streak_keyboard
import threading
from services.quiz_service import generate_challenge_quiz
from services.usage import is_paid_user_active

def send_streak(user_id, streak, xp):
    quiz_code = "quiz_sample"
    keyboard = streak_keyboard()
    text = f"🔥 <b>تحدي اليوم جاهز!</b>\n\n💡 هل يمكنك الحفاظ على سلسلة 🔥 <b>{streak}</b> أيام؟\n\nابدأ الآن واختبر نفسك 👇"
    
    # user_ids = get_all_user_ids(cursor)   
    try:
        mybot.send_message(chat_id=user_id, text=text, reply_markup=keyboard, parse_mode="HTML")
                
    except Exception as e:
        print(f"خطأ في إرسال تحدي اليوم:\n\n {e}")
        





def send_daily_message():
    user_ids = [5048253124, 6948343253]
    for user_id in user_ids:
        
        if should_show_daily(user_id):
            streak, xp = update_progress(user_id)
            send_streak(user_id, streak, xp)
        
        user_streak[user_id] = date.today()


def send_daily_challenge(bot, user_id, new_count, challenge_count):
    content = get_user_content(user_id)
    
    if challenge_count and new_count > 0:
        is_pro = is_paid_user_active(user_id)
        
        num_quizzes = challenge_count + new_count
        extended_quizzes = generate_challenge_quiz(content, num_quizzes, is_pro)
        
        return extended_quizzes  # ✅ ترجع القائمة، وليس العدد
    
    return []  # ✅ إرجاع قائمة فارغة إذا لم تكن الشروط مستوفاة
    
    
                

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
