# main.py
import os

from bot.bot_instance import bot, set_webhook
from bot.handlers import start
from bot.handlers import text_handler
from bot.handlers import file_handler
from bot.handlers import callback_handler
from bot.handlers import pre_checkout_query_handler
from bot.handlers import payment_handler
from storage.sqlite_db import init_db
from bot import flask


# تحميل مفاتيح API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# تسجيل الهاندلرز
start.register(bot)
text_handler.register(bot)
file_handler.register(bot)
callback_handler.register(bot)
pre_checkout_query_handler.register_payment(bot)
payment_handler.register(bot)

# تسجيل Flask
flask.register()

# تهيئة قاعدة البيانات
init_db()


set_webhook()

port = int(os.environ.get("PORT", 10000))
flask.app.run(host="0.0.0.0", port=port)
