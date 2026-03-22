from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def saved_quiz_upsell():
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("💎 ترقية إلى Pro", callback_data="upgrade_account")
        ]
    keyboard.add(*buttons)
    
    return keyboard

