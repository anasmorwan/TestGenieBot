keyboard = types.InlineKeyboardMarkup()
keyboard.add(
    types.InlineKeyboardButton("💎 ترقية إلى Pro", callback_data="upgrade_account")
)

bot.send_message(chat_id, text, reply_markup=keyboard)
