
import random

#---------------------
#    دوال التحقق    
#---------------------

def should_send_viral_message():
    stats = get_quiz_stats(quiz_code)
                
    if stats["users"] >= 3:
        return True

    return False

def should_send_analytics():
    
    stats = get_quiz_stats(quiz_code)
    
    if stats["users"] >= 3 and stats["completed"] >= 5:
        return True
    return False





#---------------------
#    إشعارات البوت
#---------------------
def send_viral_message():
    stats = get_quiz_stats(quiz_code)
    
    user_ids = get_quiz_user_ids(quiz_code)
    names = format_usernames(bot, user_ids)

    message = build_quiz_viral_message(stats, names)
    keyboard = tracking_upsell_keyboard()
                    
    bot.send_message(chat_id=creator_id, text=message, reply_markup=keyboard)





def send_analytics():
    stats = get_quiz_stats(quiz_code)
    hardest = get_hardest_question(quiz_code)
    success = get_success_rate(quiz_code)
    message = build_advanced_stats_message(stats, hardest, success)
    keyboard = tracking_upsell_keyboard()
    bot.send_message(chat_id=creator_id, text=message, reply_markup=keyboard)

    waiting_msg = bot.send_message(chat_id, "⏳ جارٍ تحليل النتائج...")
                    
    bot.edit_message_text(chat_id, message_id=waiting_msg.message_id, text=message, reply_markup=keyboard, parse_mode="HTML")
                        
