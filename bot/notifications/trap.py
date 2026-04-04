from bot.bot_instance import mybot
from services.user_trap import should_show_daily




if should_show_daily(user_id):
  mybot.send_message()
