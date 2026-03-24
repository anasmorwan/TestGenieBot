from telebot import types
from services.usage import is_paid_user_active
from storage.quiz_repository import get_user_current_quiz
from storage.messages import get_message







def publish_interactive_link(bot, target_chat_id, quiz_code, shared_by_name, watermark=True):
    announcement_text = (
        f"🧠 هل تستطيع حل هذا التحدي؟\n\n"  
        f"🚀 ابدأ الآن خلال 30 ثانية\n"
        f"🏆 هل تتفوق على أصدقائك؟\n"
    )
    
    if watermark:
        announcement_text += f"\n\n✨ مدعوم بالذكاء الاصطناعي"

    bot_username = bot.get_me().username
    start_url = f"https://t.me/{bot_username}?start=shared_{quiz_code}"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🎯 ابدأ الاختبار الآن", url=start_url))

    try:
        bot.send_message(
            chat_id=target_chat_id,
            text=announcement_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return True # نجح النشر
    except Exception as e:
        print(f"❌ خطأ أثناء النشر في القناة {target_chat_id}: {e}")
        return False # فشل النشر



def register(bot):


    # عند استقبال القناة المختارة
    @bot.message_handler(content_types=['chat_shared'])
    def handle_chat_shared(message):
        if message.chat.type != "private":
        
            return
        user_id = message.from_user.id
        shared_by = message.from_user.first_name
        chat_id_to_publish = message.chat_shared.chat_id
        request_id = message.chat_shared.request_id  # 🔥 هذا المهم

        # تحديد النوع بناءً على الزر
        if request_id == 1:
            chat_type = "القناة"
        elif request_id == 2:
            chat_type = "المجموعة"
        else:
            chat_type = "الشات"
        # 1. استرجاع الكويز الذي كان المستخدم يعمل عليه
        quiz_code = get_user_current_quiz(user_id) 
    
        if not quiz_code:
            bot.send_message(message.chat.id, "❌ حدث خطأ، لم نجد الاختبار المطلوب. حاول مرة أخرى.")
            return

        # 2. التحقق: هل المستخدم مشترك (Paid) أم مجاني؟
        if is_paid_user_active(user_id):
            # المستخدم برو: نعطيه خيار "كيف تريد النشر؟" لأننا نحترم وقته
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("📊 استطلاعات مباشرة (Native)", callback_data=f"pub:native:{quiz_code}:{chat_id_to_publish}:{chat_type}"))
            keyboard.add(types.InlineKeyboardButton("🔗 رابط تفاعلي (Interactive)", callback_data=f"pub:link:{quiz_code}:{chat_id_to_publish}:{chat_type}"))
        
            bot.send_message(message.chat.id, "✨ أنت مستخدم Pro! كيف تريد ظهور الاختبار في قناتك؟", reply_markup=keyboard)
        else:
            # المستخدم مجاني: ننشر فوراً بـ "الطريقة التفاعلية" (التي تفيدك أنت)
            publish_interactive_link(bot, chat_id_to_publish, quiz_code, shared_by, watermark=True)
        
            # رسالة نجاح في شات البوت الخاص
            bot.send_message(message.chat.id, "✅ تم نشر الاختبار في قناتك بنجاح باستخدام الرابط التفاعلي!")
        
            # تلميح للترقية (Soft Sell)
            # bot.send_message(message.chat.id, text=get_message("SHARED_QUIZ_REACTIONS"))








"""
# الهاندلر النهائي لاستقبال القناة المختارة
@bot.message_handler(content_types=['chat_shared'])
def handle_chat_shared(message):
    user_id = message.from_user.id
    chat_id_to_publish = message.chat_shared.chat_id
    
    # 1. استرجاع الكود المحفوظ (الذاكرة المؤقتة)
    quiz_code = get_user_current_quiz(user_id)
    
    # 2. إخفاء كيبورد الاختيار من شات المستخدم
    bot.send_message(message.chat.id, "⌛ جاري النشر في قناتك...", reply_markup=types.ReplyKeyboardRemove())
    
    # 3. التنفيذ الفوري (للمجاني)
    try:
        publish_interactive_link(bot, chat_id_to_publish, quiz_code, message.from_user.first_name)
        
        # 4. رسالة تأكيد للمستخدم
        bot.send_message(
            message.chat.id, 
            f"✅ تم النشر بنجاح!\n\n"
            f"💡 **نصيحة:** الطلاب الذين يضغطون على الزر سيتم توجيههم للبوت، وهذا يزيد من نقاطك في برنامج الإحالة!"
        )
        
        # تسجيل العملية في الإحصائيات
        log_quiz_share(quiz_code, user_id, message.from_user.first_name)
        
    except Exception as e:
        bot.send_message(message.chat.id, "❌ فشل النشر. تأكد أن البوت 'مشرف' (Admin) في القناة.")
"""
