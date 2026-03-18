from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def how_it_works_keyboatd():
    keyboard = InlineKeyboardMarkup()
    web_app_button = InlineKeyboardButton(
    text="📖 قراءة فورية",
    web_app=WebAppInfo(url="https://example.com/page.html") 
    )
    keyboard.add(web_app_button)
    btn_back = InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="main_menu")
    keyboard.add(btn_back)
    return keyboard
