

def more_options_keyboard()

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
