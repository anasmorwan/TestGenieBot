# bot/flask.py
import json
import threading
import telebot
from flask import Flask, request
from bot.bot_instance import BOT_TOKEN, mybot

app = Flask(__name__)

def register():

    @app.route("/", methods=["GET"])
    def home():
        return "Bot is alive", 200

    @app.route(f"/{BOT_TOKEN}", methods=["POST"])
    def webhook():
        try:
            # اقرأ النص الخام واطبعه للـ debug
            json_string = request.get_data().decode("utf-8")
            print("=== webhook received ===", flush=True)
            print(json_string, flush=True)
            update_dict = json.loads(json_string)

            # حوّل القاموس إلى كائن Update ثم أرسله لمكتبة telebot
            update = telebot.types.Update.de_json(update_dict)
            user_id = 
            # threading.Thread(target=mybot.process_new_updates, args=([update],)).start()
            add_task(0, {
                "type": "new_updates",
                "update": update_dict   # أو update.to_dict()
            })
            return "OK", 200

            

        except Exception as e:
            # طباعة الخطأ للإطلاع
            print("Webhook error:", e, flush=True)
            return "ERROR", 500


from core.task_queue import add_task
