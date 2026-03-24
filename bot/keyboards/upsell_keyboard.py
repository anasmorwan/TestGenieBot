from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def saved_quiz_upsell():
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("💎 ترقية إلى Pro", callback_data="plans")
        ]
    keyboard.add(*buttons)
    
    return keyboard

def quiz_number_limit_upsell():
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("💎 ترقية إلى Pro", callback_data="plans"),
    InlineKeyboardButton("🚀 مشاركة الإختبار", callback_data="post_quiz")

        ]
    keyboard.add(*buttons)
    
    return keyboard
    

def tracking_upsell_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("🔓 إفتح القائمة كاملة", callback_data="plans:tracking")
        ]
    keyboard.add(*buttons)
    
    return keyboard


def advance_analytics_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("🔓 إفتح القائمة كاملة", callback_data="plans")
        ]
    keyboard.add(*buttons)
    
    return keyboard
    

