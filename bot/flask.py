from flask import Flask  # ✅ استيراد الكلاس Flask بحرف كبير
from bot.bot_instance import BOT_TOKEN, bot
import requests

# واجهة Flask للفحص
app = Flask(__name__)  # ✅ استخدام Flask بحرف كبير

def register():
    @app.route('/')
    def home():
        return "البوت يعمل الآن"
    
    @app.route(f"/{BOT_TOKEN}", methods=["POST"])
    def webhook():
        json_str = request.get_data().decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK"
