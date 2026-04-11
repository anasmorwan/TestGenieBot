# main_menu.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(bot_username):
    keyboard = InlineKeyboardMarkup(row_width=1)

    buttons = [
        InlineKeyboardButton("📄 إرسل ملف", callback_data="go_generate"),
        InlineKeyboardButton("✍️ إرسل نص", callback_data="input_text"),
        InlineKeyboardButton("⚙️ المزيد", callback_data="more_options")
    ]
    keyboard.add(*buttons)
    return keyboard


def smart_ui_keyboard(mistakes):
    markup = InlineKeyboardMarkup(row_width=1)

    
    btn_mistakes = InlineKeyboardButton(f"📖 مراجعة أخطائي: {mistakes}", callback_data=f"start_challenge:mistakes_all:{mistakes}")
    btn_random_quiz = InlineKeyboardButton("🧠 اختبرني عشوائياً", callback_data=f"start_challenge:user_review")
    btn_settings = InlineKeyboardButton("⚙️ الإعدادات", callback_data=f"more_options")
    


    markup.add(btn_mistakes, btn_random_quiz, btn_settings)
    return markup
 
    
