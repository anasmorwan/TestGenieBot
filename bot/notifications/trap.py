from bot.bot_instance import mybot
from services.user_trap import should_show_daily, update_progress
from storage.sqlite_db import get_connection, get_user_content
from storage.session_store import user_streak
from datetime import timedelta, datetime, date
from bot.keyboards.actions_keyboard import streak_keyboard
from services.quiz_session_service import QuizManager
import threading
from services.quiz_service import generate_challenge_quiz
from services.usage importis_paid_user_active

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


def send_daily_challenge(bot, user_id, review_count, new_count, challenge_count):
    content = get_user_content(user_id)
    
    if challenge_count and new_count > 0:
        is_pro = is_paid_user_active(user_id)
        
        num_quizzes = challenge_count + new_count
        extended_quizzes = threading.Thread(target=generate_challenge_quiz, kwargs={
            'content': content,
            'is_pro': is_pro,
            'num_questions': num_quizzes
        }).start()
        
    if review_count > 0:
        mistakes = get_recent_mistakes(user_id, review_count)
                    
        QuizManager.start_mistakes_review(chat_id, mistakes, bot)
        
    if extended_quizzes is not None and len(extended_quizzes) > 0:
        pass
    if challenge_count > 0:
        pass

    
                

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
