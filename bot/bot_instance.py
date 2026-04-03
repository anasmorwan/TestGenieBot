import os
import telebot
from telebot import util
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

mybot = telebot.TeleBot(BOT_TOKEN, threaded=False)


def set_webhook():
    mybot.remove_webhook()
    # إضافة drop_pending_updates=True تمسح الرسائل المتراكمة القديمة
    mybot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}", drop_pending_updates=True)

    logging.info(f"🌍 Webhook set at {WEBHOOK_URL}/{BOT_TOKEN}")
    
