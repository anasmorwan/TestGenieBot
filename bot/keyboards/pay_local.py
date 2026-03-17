from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def local_upgrade_options_keyboard():

    reply_markup = InlineKeyboardMarkup(row_width=1)
  
    reply_markup.add(
        InlineKeyboardButton("💬 تواصل معنا", url="https://t.me/anasM2002"),
        InlineKeyboardButton("🔙 رجوع", callback_data="go_account_settings")
    )
    return reply_markup
