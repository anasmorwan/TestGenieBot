def backup_to_telegram(bot, admin_chat_id):
    with open("quiz_users.db", "rb") as f:
        bot.send_document(admin_chat_id, f, caption="📦 Backup DB")
