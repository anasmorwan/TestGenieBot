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
    


def scheduled_quiz_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    keyboard.add(
        InlineKeyboardButton("⏰ كل ساعة", callback_data="hourly_quiz"),
        InlineKeyboardButton("📆 كل يوم", callback_data="daily_quiz")     
    )
    keyboard.add(
        InlineKeyboardButton("🔒 مخصص", callback_data="adjusted_quiz")
    )   
    return keyboard






def manual_selection_keyboard():
    """لوحة الأرقام"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    keyboard.add(
        InlineKeyboardButton("1️⃣", callback_data="num_1"),
        InlineKeyboardButton("2️⃣", callback_data="num_2"),
        InlineKeyboardButton("3️⃣", callback_data="num_3")
    )
    
    keyboard.add(
        InlineKeyboardButton("4️⃣", callback_data="num_4"),
        InlineKeyboardButton("5️⃣", callback_data="num_5"),
        InlineKeyboardButton("6️⃣", callback_data="num_6")
    )
    
    keyboard.add(
        InlineKeyboardButton("7️⃣", callback_data="num_7"),
        InlineKeyboardButton("8️⃣", callback_data="num_8"),
        InlineKeyboardButton("9️⃣", callback_data="num_9")
    )
    
    keyboard.add(
        InlineKeyboardButton("0️⃣", callback_data="num_0")
    )
    
    keyboard.add(
        InlineKeyboardButton("🗑️ مسح الكل", callback_data="num_clear_all"),
        InlineKeyboardButton("⌫ حذف", callback_data="num_delete"),
        InlineKeyboardButton("✅ تأكيد", callback_data="num_confirm")
    )
    
    keyboard.add(
        InlineKeyboardButton("❌ إلغاء", callback_data="num_cancel")
    )
    
    return keyboard


