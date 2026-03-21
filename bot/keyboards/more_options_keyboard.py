

def more_options_keyboard()
    keyboard = keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("🎲 اختبار عشوائي", callback_data="quick_quiz"),
        InlineKeyboardButton("⭐ TestGenie Pro", callback_data="upgrade_account"),
        InlineKeyboardButton("👤 حسابي", callback_data="go_account_settings"),
        InlineKeyboardButton("➕ أضفني إلى مجموعة", url=f"https://t.me/{bot_username}?startgroup=true"),
        InlineKeyboardButton("❓ كيف يعمل؟", callback_data="how_it_works"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    ]
    keyboard.add(*buttons)
    return keyboard
