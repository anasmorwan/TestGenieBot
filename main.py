# main.py
from bot.bot_instance import bot
import bot.handlers.start  # يستورد /start handler

bot.polling()