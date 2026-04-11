# quiz_keyboard

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def quiz_keyboard(quiz_code):
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    
    InlineKeyboardButton("​🚀 نشر في القناة", callback_data=f"post_quiz:{quiz_code}")
        ]
    keyboard.add(*buttons)
    
    return keyboard


def share_quiz_button(quiz_code):
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("​👥+📤 مشاركة", callback_data=f"post_quiz:{quiz_code}"),
    InlineKeyboardButton("🔄 إعادة", callback_data=f"start_quiz:{quiz_code}")
        ]
    keyboard.add(*buttons)
    
    return keyboard


def smart_ui_keyboard(mistakes):
    markup = InlineKeyboardMarkup(row_width=1)

    
    btn_mistakes = InlineKeyboardButton(f"📖 مراجعة أخطائي: {mistakes}", callback_data=f"start_challenge:mistakes:{mistakes}")
    btn_random_quiz = InlineKeyboardButton("🧠 اختبرني عشوائياً", callback_data=f"questions_quiz")
    btn_settings = InlineKeyboardButton("⚙️ الإعدادات", callback_data=f"questions_quiz")
    


    markup.add(btn_mistakes, btn_random_quiz, btn_settings)
    return markup




def too_mistakes_keyboard(wrong_count, ad_compaign=False, campaign_link=None):
    keyboard = InlineKeyboardMarkup(row_width=1)
    if ad_compaign:
        buttons = [ 
            InlineKeyboardButton("🎯 تدريب على أخطائي", callback_data=f"start_challenge:mistakes:{wrong_count}"),
            InlineKeyboardButton("👈 جرب الآن", link=f"{campaign_link}")
        ]
    buttons = [ 
    InlineKeyboardButton("🎯 تدريب على أخطائي", callback_data=f"start_challenge:mistakes:{wrong_count}")
        ]
    keyboard.add(*buttons)
    
    return keyboard



def few_mistakes_keyboard(wrong_count, ad_compaign=False, campaign_link=None):
    keyboard = InlineKeyboardMarkup(row_width=1)
    if ad_compaign:
        buttons = [ 
            InlineKeyboardButton("🔥 جربه الآن", link=f"{campaign_link}"),
            InlineKeyboardButton("🧠 راجع أخطائي", callback_data=f"start_challenge:mistakes:{wrong_count}")
        ]
    buttons = [ 
        InlineKeyboardButton("🔥 تحدي جديد", callback_data="go_generate"),
        InlineKeyboardButton("🧠 راجع أخطائي", callback_data=f"start_challenge:mistakes:{wrong_count}")
    ]
    keyboard.add(*buttons)
    
    return keyboard
    
def pro_quota_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    buttons = [ 
    InlineKeyboardButton("🔥 جرب الآن", callback_data="pro_quota")
        ]
    keyboard.add(*buttons)
    
    return keyboard
    
