from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def account_status_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    ref_code = user_id

    btn_update = InlineKeyboardButton(text="🔁 تحديث", callback_data="update_account_status")
    btn_refer = InlineKeyboardButton(text="👥 دعوة صديق", url=f"https://t.me/share/url?url=https://t.me/testprog123bot?start=ref_{ref_code}&text=🔥 جرب هذا البوت! يحول أي ملف لاختبار تفاعلي خلال ثواني")  
    btn_upgrade = InlineKeyboardButton("🚀 ترقية الحساب", callback_data="upgrade_account")
    btn_back = InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    

    markup.add(btn_update, btn_refer, btn_upgrade, btn_back)
    return markup

def plan_update_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    ref_code = user_id

    btn_update = InlineKeyboardButton(text="🔁 تحديث", callback_data="update_account_status")
    btn_refer = InlineKeyboardButton(text="👥 دعوة صديق", url=f"https://t.me/share/url?url=https://t.me/testprog123bot?start=ref_{ref_code}&text=🔥 جرب هذا البوت! يحول أي ملف لاختبار تفاعلي خلال ثواني")  
    btn_upgrade = InlineKeyboardButton("🚀 ترقية الحساب", callback_data="upgrade_account")
    btn_back = InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    

    markup.add(btn_update, btn_refer, btn_upgrade, btn_back)
    return markup


def account_status_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    ref_code = user_id

    btn_update = InlineKeyboardButton(text="🔁 تحديث", callback_data="update_account_status")
    btn_refer = InlineKeyboardButton(text="👥 دعوة صديق", url=f"https://t.me/share/url?url=https://t.me/testprog123bot?start=ref_{ref_code}&text=🔥 جرب هذا البوت! يحول أي ملف لاختبار تفاعلي خلال ثواني")  
    btn_upgrade = InlineKeyboardButton("🚀 ترقية الحساب", callback_data="upgrade_account")
    btn_back = InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    

    markup.add(btn_update, btn_refer, btn_upgrade, btn_back)
    return markup

def plan_update_keyboard_pro(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    ref_code = user_id

    btn_update = InlineKeyboardButton(text="🔁 تحديث", callback_data="update_account_status")
    btn_refer = InlineKeyboardButton(
    text="👥 دعوة صديق",
    url=f"https://t.me/share/url?url=https://t.me/testprog123bot?start=ref_{ref_code}&text=🔥 جرب بوت Qube - يحول أي ملف إلى اختبار تفاعلي خلال ثواني! 🚀"
    )

    btn_back = InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    

    markup.add(btn_update, btn_refer, btn_back)
    return markup

