# main.py
from bot.bot_instance import bot



import bot.handlers.start  # يستورد /start handler
import bot.handlers.text_handler
import bot.handlers.file_handler
from storage.sqlite_db import init_db




text_handler.register(bot)
file_handler.register(bot)

bot.infinity_polling()


init_db()
