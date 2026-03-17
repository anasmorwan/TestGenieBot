from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def account_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)

    btn_status = InlineKeyboardButton("🔎 معرفة حالة حسابي", callback_data="check_account_status")
    btn_upgrade = InlineKeyboardButton("🚀 ترقية الحساب", callback_data="upgrade_account")
    btn_back = InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")


    markup.add(btn_status, btn_upgrade, btn_back)
    return markup

