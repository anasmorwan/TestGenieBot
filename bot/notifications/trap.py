from bot.bot_instance import mybot
from services.user_trap import should_show_daily, get_inactivity_level, update_progress, get_user_content, is_inactive
from storage.sqlite_db import get_connection, build_dynamic_message, get_last_branches
from storage.session_store import user_streak
from datetime import timedelta, datetime, date
from bot.keyboards.actions_keyboard import streak_keyboard
import threading
from services.quiz_service import generate_challenge_quiz
from services.usage import is_paid_user_active
from storage.messages import get_message
import random


def send_daily_challenge_message():
    conn = get_connection()
    cursor = conn.cursor
    user_ids = [5048253124, 6948343253]
    for user_id in user_ids:
        
        if is_inactive(user_id):
            streak, xp = update_progress(user_id)
            keyboard = streak_keyboard()
            status = get_inactivity_level(user_id)
            text = get_message("NEW_USER_STREAK")
            branches = get_last_branches(cursor, user_id)
            clean_branches = [b[0] for b in branches if b[0]]
            conn.close()
    
            
            
            if status == "new":
                text = random.choice([get_message("NEW_USER_STREAK", streak=streak), get_message("USER_STREAK", streak=streak)])
            
            if status == "active":
                if clean_branches:
                    if random.random() < 0.8:  # 80% للخيار الثاني
                        text = build_dynamic_message(user_id)
                    else:
                        text = random.choice([get_message("ACTIVE_USER_STREAK", streak=streak), get_message("RETURNING_USER_STREAK")])
                        
                text = random.choice([get_message("ACTIVE_USER_STREAK", streak=streak), build_dynamic_message(user_id), get_message("RETURNING_USER_STREAK")])
                if text is False:
                    text = get_message("ACTIVE_USER_STREAK")
                
                
            elif status == "cooling":
                if clean_branches:
                    if random.random() < 0.8:  # 80% للخيار الثاني
                        text = build_dynamic_message(user_id)
                    else:
                        text = random.choice([get_message("COOLING_USER_STREAK", streak=streak), get_message("COOLING_USER_STREAK1", streak=streak)])
            
                text = build_dynamic_message(user_id)
                if text is False:
                    text = random.choice([get_message("COOLING_USER_STREAK", streak=streak), get_message("COOLING_USER_STREAK1", streak=streak)])
            

            elif status == "inactive":
                text = build_dynamic_message(user_id)
                if text is False:
                    text = get_message("INACTIVE_USER_STREAK", streak=streak)
                
            elif status == "lost":
                text = build_dynamic_message(user_id)
                if text is False:
                    text = get_message("INACTIVE_USER_STREAK", streak=streak)
                
                
                
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
