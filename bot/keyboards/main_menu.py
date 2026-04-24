# main_menu.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)

    buttons = [
        InlineKeyboardButton("🚀 ابدأ تحدي اليوم", callback_data=f"today_quiz:{user_id}"),
        InlineKeyboardButton("📄 ارفع ملخصي", callback_data="go_generate")
    ]
    keyboard.add(*buttons)
    return keyboard


def smart_ui_keyboard(mistakes):
    markup = InlineKeyboardMarkup(row_width=1)
    # start_challenge:user_review
    # callback_data=f"share_quizzes
    btn_settings = InlineKeyboardButton("⫶ المزيد", callback_data="more_options")
    btn_random_quiz = InlineKeyboardButton("📆 إمتحان شامل", callback_data=f"start_challenge:user_review")
    btn_mistakes = InlineKeyboardButton(f"📖 مراجعة أخطائي: {mistakes} (خليط ذكي)", callback_data=f"start_challenge:mistakes_all:{mistakes}")


    markup.add(btn_mistakes, btn_random_quiz, btn_settings)
    return markup
 
    
def ui_no_mistakes_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)


    btn_random_quiz = InlineKeyboardButton("🧠 اختبرني عشوائياً", callback_data=f"start_challenge:user_review")
    btn_settings = InlineKeyboardButton("⚙️ الإعدادات", callback_data="more_options")
    


    markup.add(btn_random_quiz, btn_settings)
    return markup
 

