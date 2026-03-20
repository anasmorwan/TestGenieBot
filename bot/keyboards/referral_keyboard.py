from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def referral_keyboard(user_id):
    ref_code = user_id
    invite_link = f"https://t.me/testprog123bot?start=ref_{ref_code}"
    referal_btns = InlineKeyboardMarkup(row_width=1)
    
    referal_btns.add(
    InlineKeyboardButton(text="👥 دعوة صديق", url=f"https://t.me/share/url?url=https://t.me/testprog123bot?start=ref_{ref_code}&text=🔥 جرب هذا البوت! يحول أي ملف لاختبار تفاعلي خلال ثواني"), 
    InlineKeyboardButton(text="📋 نسخ رابطي", callback="copylink")
    )
    
    return referal_btns
    
   
