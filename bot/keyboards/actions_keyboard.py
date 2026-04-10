from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def send_poll_keyboard(poll_code):
    markup = InlineKeyboardMarkup(row_width=1)
    # regenerate:{temp_text}
    btn_post = InlineKeyboardButton("🚀 نشر في القناة", callback_data=f"post_poll:{poll_code}")
    btn_regenerate = InlineKeyboardButton("🔄 إعادة توليد", callback_data=f"customize_poll")

    

    markup.add(btn_post, btn_regenerate)
    return markup

def escape_action_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    
    btn_cancel = InlineKeyboardButton("× إلغاء", callback_data=f"cancel")

    

    markup.add(btn_cancel)
    return markup

def quiz_refill_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    
    btn_refill = InlineKeyboardButton("✅ نعم أريد", callback_data=f"refill_quiz")
    btn_new_quiz = InlineKeyboardButton("أريد إختبار جديد", callback_data=f"questions_quiz")
    
    

    markup.add(btn_refill, btn_new_quiz)
    return markup
                                  
def streak_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    
    btn_refill = InlineKeyboardButton("🔥 إبدأ التحدي", callback_data=f"start_challenge")
    

    markup.add(btn_refill)
    return markup

    
