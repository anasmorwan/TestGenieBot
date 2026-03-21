from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def post_to(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    ref_code = user_id


    btn_postgroup = InlineKeyboardButton("👥 إرسال لمجموعة (مجاني)", callback_data="upgrade_account")
    btn_postchannel = InlineKeyboardButton("📢 نشر في قناة (للمديرين)", callback_data="main_menu")
    btn_back = InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    

    markup.add(btn_refer, btn_upgrade, btn_back)
    return markup


def post_to_channel(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    ref_code = user_id


    btn_deep_link = InlineKeyboardButton("🔗 رابط اختبار تفاعلي (مجاني)", callback_data="upgrade_account")
    btn_polls = InlineKeyboardButton("📊 نشر كاستطلاعات متتالية 🔒 (Pro)", url=f"https://t.me/share/url?url=https://t.me/testprog123bot?start=ref_{ref_code}&text=🔥 جرب هذا البوت! يحول أي ملف لاختبار تفاعلي خلال ثواني") 
    btn_back = InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")

    markup.add(btn_refer, btn_upgrade, btn_back)
    return markup
