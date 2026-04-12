import os
from services.usage import activate_subscription_manual, reset_or_set_daily_usage, get_user_full_info
from analytics.metrics import get_metrics
from services.backup_service import backup_all


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
            backup_all()

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
            backup_all()

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


    @bot.message_handler(commands=["knowledge"])
    def view_user_knowledge(msg):
        """الأمر: /knowledge <user_id> - يعرض النصوص المحفوظة لمستخدم معين"""
    
        user_id = msg.from_user.id
        
    
        # التحقق من صلاحيات الأدمن
        if user_id not in admin_ids:
            bot.reply_to(msg, "⛔ هذا الأمر مخصص للأدمن فقط.")
            return
    
        # استخراج معرف المستخدم من الأمر
        parts = msg.text.split()
    
        if len(parts) < 2:
            bot.reply_to(
                msg, 
                "❌ الرجاء إدخال معرف المستخدم.\n\n"
                "مثال: `/knowledge 123456789`",
                parse_mode="Markdown"
            )
            return
    
        # التحقق من أن المعرف رقم
        try:
            target_user_id = int(parts[1])
        except ValueError:
            bot.reply_to(msg, "❌ معرف المستخدم يجب أن يكون رقماً.")
            return
    
        # جلب البيانات من قاعدة البيانات
        try:
            knowledge_data = get_user_knowledge(target_user_id)
        
            if not knowledge_data:
                bot.reply_to(
                    msg,
                    f"📭 لا توجد نصوص محفوظة للمستخدم `{target_user_id}`.",
                    parse_mode="Markdown"
                )
                return
        
            # بناء الرسالة
            message = f"📚 **نصوص المستخدم المحفوظة**\n"
            message += f"👤 **المعرف:** `{target_user_id}`\n"
            message += f"📊 **عدد النصوص:** {len(knowledge_data)}\n"
            message += f"{'─' * 30}\n\n"
        
            for i, record in enumerate(knowledge_data, 1):
                record_id = record.get('id')
                last_text = record.get('last_text', 'لا يوجد نص')
                specialty = record.get('specialty', 'غير محدد')
                updated_at = record.get('updated_at', 'غير معروف')
            

                # ✅ استخدام دالة الاختصار: السطر الأول فقط، بحد أقصى 100 حرف
                last_text = truncate_text(last_text, max_length=100, keep_first_line=True)
            
                message += f"**{i}.** 🆔 سجل رقم: `{record_id}`\n"
                message += f"   📝 **النص:** {last_text}\n"
                message += f"   🏷️ **التخصص:** `{specialty}`\n"
                message += f"   🕒 **آخر تحديث:** `{updated_at}`\n"
                message += f"   {'.' * 20}\n\n"
            
                # تجنب تجاوز حد طول الرسالة (4096 حرف)
                if len(message) > 3800 and i < len(knowledge_data):
                    bot.reply_to(msg, message, parse_mode="Markdown")
                    message = f"📚 **نصوص المستخدم المحفوظة (تابع)**\n\n"
        
            bot.reply_to(msg, message, parse_mode="Markdown")
        
        except Exception as e:
            bot.reply_to(msg, f"❌ حدث خطأ أثناء جلب البيانات: {str(e)}")



    @bot.message_handler(commands=['bot_chats_report'])
    def send_report(message):
        try:
            if not joined_chats:
                bot.reply_to(message, "📊 لا توجد قنوات أو مجموعات مسجلة بعد.\n\n💡 تأكد من أن البوت تمت إضافته كـ Admin في القنوات/المجموعات وأنك فعّالت خاصية جمع المعلومات.")
                return
    
            total = len(joined_chats)
            report_text = f"<b>📊 تقرير القنوات والمجموعات</b>\n\n"
            report_text += f"<b>📌 العدد الإجمالي:</b> {total}\n\n"
            report_text += "<b>📋 القائمة:</b>\n"
    
            for idx, (chat_id, chat_info) in enumerate(list(joined_chats.items())[:20], 1):  # عرض أول 20 فقط
                chat_type = "📢 قناة" if chat_info.get('type') == 'channel' else "👥 مجموعة"
                chat_title = chat_info.get('title', 'بدون اسم')
                report_text += f"{idx}. {chat_type} | <b>{chat_title}</b>\n"
                report_text += f"   🆔 <code>{chat_id}</code>\n\n"
    
            if total > 20:
                report_text += f"\n... و {total - 20} أخرى"
    
            bot.reply_to(message, report_text, parse_mode="HTML")
    
        except Exception as e:
            bot.reply_to(msg, f"❌ حدث خطأ أثناء جلب البيانات: {str(e)}")
            
