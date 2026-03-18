from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def how_it_works_keyboatd():
    keyboard = InlineKeyboardMarkup(row_width=1)

    web_app_button = InlineKeyboardButton(
    text="⚡ كيف يعمل؟",
    url="https://example.com/how-it-works"
    )
    keyboard.add(web_app_button)
    btn_back = InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    keyboard.add(btn_back)
    return keyboard
