from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def referral_keyboard(user_id):
    ref_code = user_id
    referal_btns = InlineKeyboardMarkup(row_width=1)
    
    referal_btns.add(
    InlineKeyboardButton(text="👥 دعوة صديق", url=f"https://t.me/share/url?url=https://t.me/testprog123bot?start={ref_code}&text=🔥 جرب هذا البوت! يحول أي ملف لاختبار تفاعلي خلال ثواني"), 
    InlineKeyboardButton(text="📋 نسخ رابطي", callback_data="copy_invite")
    )
    return referal_btns
    
   
