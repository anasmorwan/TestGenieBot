from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def how_it_works_keyboatd():
    keyboard = InlineKeyboardMarkup()
    web_app_button = InlineKeyboardButton(
    text="📖 قراءة فورية",
    web_app=WebAppInfo(url="https://example.com/page.html") 
    )
    keyboard.add(web_app_button)
    keyboard.add(InlineKeyboardButton("
    return keyboard
