# main_menu.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(bot_username):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        # الصف الأول: العمليات الأساسية
        [
            InlineKeyboardButton("📝 نص مباشر", callback_data="input_text"),
            InlineKeyboardButton("📎 إرسال ملف", callback_data="go_generate")
        ],
        # الصف الثاني: التفاعل السريع والشرح
        [
            InlineKeyboardButton("⚡ اختبار عشوائي", callback_data="quick_quiz"),
            InlineKeyboardButton("📖 كيف يعمل؟", callback_data="how_it_works")
        ],
        # الصف الثالث: الحساب والترقية
        [
            InlineKeyboardButton("👤 حسابي", callback_data="go_account_settings"),
            InlineKeyboardButton("🚀 TestGenie Pro", callback_data="upgrade_pro")
        ]
    ]

    keyboard.add(*buttons)
    keyboard.add(
        InlineKeyboardButton("➕ أضفني إلى مجموعة", url=f"https://t.me/{bot_username}?startgroup=true")
        )
    return keyboard
