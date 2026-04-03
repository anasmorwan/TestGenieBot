import os
import telebot
from telebot import util
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

mybot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)


def set_webhook():
    mybot.remove_webhook()
    mybot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    logging.info(f"🌍 Webhook set at {WEBHOOK_URL}/{BOT_TOKEN}")
    
