from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def more_options_keyboard(bot_username):
    keyboard = keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("📆 جدولة إختبار", callback_data="scheduled_quiz"),
        InlineKeyboardButton("⭐ Qube Pro", callback_data="upgrade_account"),
        InlineKeyboardButton("👤 حسابي", callback_data="go_account_settings"),
        InlineKeyboardButton("➕ أضفني إلى مجموعة", url=f"https://t.me/{bot_username}?startgroup=true"),
        InlineKeyboardButton("❓ كيف يعمل؟", callback_data="how_it_works"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    ]
    keyboard.add(*buttons)
    return keyboard
