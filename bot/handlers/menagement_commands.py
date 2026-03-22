import os
from services.usage import activate_subscription_manual, reset_or_set_daily_usage, get_user_full_info
from analytics.metrics import get_metrics

ADMIN_ID = int(os.getenv("ADMIN_ID"))

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

        except Exception as e:
            bot.reply_to(msg, f"❌ استخدم: /give_pro user_id pro\nالخطأ: {str(e)}")


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

        except Exception as e:
            bot.reply_to(msg, f"❌ استخدم: /reset_usage user_id 3\nالخطأ: {str(e)}")

    

    @bot.message_handler(commands=["user_info"])
    def user_info(msg):
        if msg.from_user.id != ADMIN_ID:
            return

        try:
            _, user_id = msg.text.split()
            user_id = int(user_id)

            data = get_user_full_info(user_id)

            user = data["user"]
            sub = data["sub"]

            if not user:
                bot.reply_to(msg, "❌ المستخدم غير موجود")
                return

            used_today, daily_limit, created_at = user

            if sub:
                plan, expires_at, quiz_limit, ocr_limit = sub
            else:
                plan, expires_at, quiz_limit, ocr_limit = ("free", None, 3, 1)

            text = f"""
📊 <b>User Info</b>

🆔 ID: <code>{user_id}</code>

👤 Plan: <b>{plan}</b>
⚡ Used Today: {used_today} / {quiz_limit}
📅 Expires: {expires_at or "N/A"}

🎁 Referrals: {data['referrals']}

📆 Joined: {created_at}
"""

            bot.reply_to(msg, text, parse_mode="HTML")

        except:
            bot.reply_to(msg, "❌ استخدم: /user_info 123456")



    @bot.message_handler(commands=["metrics"])
    def metrics(msg):
        if msg.from_user.id != ADMIN_ID:
            return

        try:

            data = get_metrics()

            text = f"""
📊 <b>TestGenie Metrics</b>

👥 Total Users: {data['users']}
⚡ Active Today: {data['active_today']}

🔥 Hit Limit: {data['hit_limit']}
💎 Paid Users: {data['paid']}

🎁 Referrals: {data['referrals']}
"""

            bot.reply_to(msg, text, parse_mode="HTML")
        except Exception as e:
            bot.reply_to(msg, f"❌ الخطأ: {str(e)}")

