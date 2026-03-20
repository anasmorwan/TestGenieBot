from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def account_status_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)


    btn_upgrade = InlineKeyboardButton("🚀 ترقية الحساب", callback_data="upgrade_account")
    btn_back = InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    btn_refer = InlineKeyboardButton(text="👥 دعوة صديق", url=f"https://t.me/share/url?url=https://t.me/testprog123bot?start=ref_{ref_code}&text=🔥 جرب هذا البوت! يحول أي ملف لاختبار تفاعلي خلال ثواني") 


    markup.add(btn_upgrade, btn_back, btn_refer)
    return markup

