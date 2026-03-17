from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def upgrade_options_keyboard():

    reply_markup = InlineKeyboardMarkup(row_width=1)
  
    reply_markup.add(
        InlineKeyboardButton("💬 تواصل معنا", url="https://t.me/anasM2002"),
        InlineKeyboardButton("🔙 رجوع", callback_data="upgrade_back")
    )
    return reply_markup
