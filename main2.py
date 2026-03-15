# main.py
from bot.bot_instance import bot
from bot.bot_instance import set_webhook

import bot.handlers.pre_checkout_query_handler
import bot.handlers.start  # يستورد /start handler
import bot.handlers.text_handler
import bot.handlers.file_handler
from storage.sqlite_db import init_db
import bot.handlers.callback_handler



text_handler.register(bot)
file_handler.register(bot)
callback_handler.register(bot)
pre_checkout_query_handler.register_payment(bot)
set_webhook()


init_db()
