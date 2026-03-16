# main.py
import os
from bot.bot_instance import bot
from bot.bot_instance import set_webhook

from bot.handlers import pre_checkout_query_handler
from bot.handlers import start  # يستورد /start handler
from bot.handlers import text_handler
from bot.handlers import file_handler
from storage.sqlite_db import init_db
from bot.handlers import callback_handler
from bot.handlers import payment_handler
from bot import flask 


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

text_handler.register(bot)
file_handler.register(bot)
callback_handler.register(bot)
pre_checkout_query_handler.register_payment(bot)
payment_handler.register(bot)
flask.register()


if __name__ == __main__:
set_webhook()


init_db()
