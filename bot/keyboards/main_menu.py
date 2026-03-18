# main_menu.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(bot_username):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.row(
        InlineKeyboardButton("📝 نص مباشر", callback_data="input_text"),
        InlineKeyboardButton("📎 إرسال ملف", callback_data="go_generate")
    )

    keyboard.row(
        InlineKeyboardButton("⚡ اختبار عشوائي", callback_data="quick_quiz"),
        InlineKeyboardButton("📖 كيف يعمل؟", callback_data="how_it_works")
    )

    keyboard.row(
        InlineKeyboardButton("👤 حسابي", callback_data="go_account_settings"),
        InlineKeyboardButton("🚀 TestGenie Pro", callback_data="upgrade_account")
    )

    keyboard.add(
        InlineKeyboardButton("➕ أضفني إلى مجموعة", url=f"https://t.me/{bot_username}?startgroup=true")
    )

    return keyboard
