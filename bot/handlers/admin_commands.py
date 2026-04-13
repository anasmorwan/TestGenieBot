import os
from services.usage import activate_subscription_manual, reset_or_set_daily_usage, get_user_full_info
from analytics.metrics import get_metrics
from services.backup_service import backup_all

from storage.sqlite_db import flush_to_db, get_chats_stats, get_all_chats
from bot.handlers.group_messages_handler import buffer_lock
from storage.session_store import message_buffer

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
        
    
        if user_id != ADMIN_ID:
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



    @bot.message_handler(commands=['list_chats'])
    def list_chats(message: Message):
        
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ غير مصرح لك بهذا الأمر")
            return
        
        # حفظ البافر أولاً للحصول على أحدث البيانات
        flush_to_db()
        
        chats = get_all_chats()
        stats = get_chats_stats()
        
        if not chats:
            bot.reply_to(message, "📭 لا توجد شاتات مسجلة حتى الآن")
            return
        
        response = f"📊 **إحصائيات عامة:**\n"
        response += f"• إجمالي الشاتات: {stats['total']}\n"
        response += f"• قنوات: {stats['channels']}\n"
        response += f"• مجموعات: {stats['groups']}\n"
        response += f"• إجمالي الرسائل: {stats['messages']}\n\n"
        
        response += f"📋 **قائمة الشاتات (آخر {min(10, len(chats))}):**\n"
        
        for chat in chats[:10]:
            response += f"\n• **{chat[2]}** ({chat[4]})\n"
            response += f"  🆔 ID: `{chat[1]}`\n"
            if chat[3]:
                response += f"  📢 Username: @{chat[3]}\n"
            response += f"  💬 الرسائل: {chat[6]}\n"
            response += f"  📅 تاريخ الإضافة: {chat[8][:10]}\n"
        
        bot.reply_to(message, response, parse_mode='Markdown')
    
    # أمر لإظهار إحصائيات البافر (للمطور)
    @bot.message_handler(commands=['buffer_stats'])
    def buffer_stats(message: Message):
        
        if message.from_user.id != ADMIN_ID:
            return
        
        with buffer_lock:
            response = f"📊 **حالة البافر الحالية:**\n\n"
            response += f"📝 رسائل في البافر: {len(message_buffer)} شات\n"
            response += f"💾 شاتات جديدة: {len(chats_buffer)}\n"
            response += f"📈 إجمالي الرسائل المعلقة: {sum(message_buffer.values())}\n"
            
            if message_buffer:
                response += f"\n**أكثر 5 شاتات نشاطاً:**\n"
                sorted_chats = sorted(message_buffer.items(), key=lambda x: x[1], reverse=True)[:5]
                for chat_id, count in sorted_chats:
                    response += f"• شات {chat_id}: {count} رسالة\n"
        
        bot.reply_to(message, response, parse_mode='Markdown')

    # أمر يدوي لحفظ البافر
    @bot.message_handler(commands=['flush'])
    def force_flush(message: Message):
    
    
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ غير مصرح")
            return
    
        flush_to_db()
        bot.reply_to(message, "✅ تم حفظ البافر في قاعدة البيانات")


