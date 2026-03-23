# quiz_keyboard

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def quiz_keyboard(quiz_code):
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("📝 إبدأ", callback_data=f"start_quiz:{quiz_code}"),
    InlineKeyboardButton("​🚀 نشر في القناة", callback_data=f"post_quiz:{quiz_code}")
        ]
    keyboard.add(*buttons)
    
    return keyboard


def share_quiz_button(quiz_code):
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("​👥+📤 مشاركة", callback_data=f"post_quiz:{quiz_code}")
        ]
    keyboard.add(*buttons)
    
    return keyboard
