

def register(bot):
    
    @bot.message_handler(commands=["give_pro"])
    def give_pro(msg):
        if msg.from_user.id != ADMIN_ID:
            return

        try:
            _, user_id, plan = msg.text.split()
            user_id = int(user_id)

            activate_subscription_manual(user_id, plan)

            bot.reply_to(msg, "✅ تم تفعيل الاشتراك")

        except:
            bot.reply_to(msg, "❌ استخدم: /give_pro user_id pro")


    @bot.message_handler(commands=["reset_usage"])
    def reset_usage(msg):
        if msg.from_user.id != ADMIN_ID:
            return

        try:
            _, user_id, limit = msg.text.split()
            user_id = int(user_id)
            limit = int(limit)

            reset_or_set_daily_usage(user_id, limit)

            bot.reply_to(msg, "✅ تم إعادة ضبط الاستخدام")

        except:
            bot.reply_to(msg, "❌ استخدم: /reset_usage user_id 3")
