# main.py (مهم: وضع طباعات للتتبع)
import os
from bot.bot_instance import bot, set_webhook
from bot.handlers import start, text_handler, file_handler, callback_handler, pre_checkout_query_handler, payment_handler
from storage.sqlite_db import init_db
from bot.handlers import poll_answer_handler
from bot import flask
from services.backup_service import restore_if_needed, start_auto_backup





print("main starting...", flush=True)

# تسجيل الهاندلرز
start.register(bot); print("start.register done", flush=True)
text_handler.register(bot); print("text_handler.register done", flush=True)
file_handler.register(bot); print("file_handler.register done", flush=True)
callback_handler.register(bot); print("callback_handler.register done", flush=True)
pre_checkout_query_handler.register_payment(bot); print("pre_checkout_query_handler.register done", flush=True)
payment_handler.register(bot); print("payment_handler.register done", flush=True)
poll_answer_handler.register(bot)



# سجل الويب هوك داخلياً
flask.register(); print("flask.register done", flush=True)

init_db(); print("init_db done", flush=True)

# ضع webhook ثم شغّل Flask
set_webhook(); print("set_webhook done", flush=True)

restore_if_needed()
init_db()

start_auto_backup(bot)


port = int(os.environ.get("PORT", 10000))
print(f"Starting Flask on port {port}", flush=True)
flask.app.run(host="0.0.0.0", port=port)
