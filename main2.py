# main.py
from bot.bot_instance import bot



import bot.handlers.start  # يستورد /start handler
from bot.handlers.text_handler import register
from bot.handlers.file_handler import file_handler
from storage.sqlite_db import init_db




start_handler.register(bot)
file_handler.register(bot)

bot.infinity_polling()


init_db()
