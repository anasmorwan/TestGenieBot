from bot.bot_instance import mybot
from services.user_trap import should_show_daily
from storage.sqlite_db import get_connection


if should_show_daily(user_id):
    user_ids = get_all_user_ids(cursor)
    for user_id in user_ids
    mybot.send_message(chat_id =user_id, "🔥 تحدي اليوم جاهز!")


def get_all_user_ids():
    conn = get_connection
    cursor = conn.cursor()
  
    try:
        cursor.execute("SELECT user_id FROM users")
        results = cursor.fetchall()
        return [row[0] for row in results]
    except Exception as e:
        print(f"خطأ في استرجاع user_ids: {e}")
        return []
