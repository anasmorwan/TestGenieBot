from telebot import types
from services.usage import is_paid_user_active
from storage.quiz_repository import get_user_current_selection

def register(bot):

    # دالة صياغة الرسالة الإعلانية التي ستنشر في القناة
    def publish_interactive_link(bot, target_chat_id, quiz_code, shared_by_name, watermark=True):
        """
        تنشر رسالة إعلانية جذابة في القناة/المجموعة تحتوي على زر لبدء الاختبار.
        """
        # 1. تجهيز النص التنسيقي (Markdown)
        # استخدمنا الرموز التعبيرية (Emojis) لجعل الرسالة "حية"
        announcement_text = (
            f"🧠 **اختبار جديد متاح الآن!**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 **بواسطة:** {shared_by_name}\n"
            f"📝 **النوع:** اختبار ذكاء اصطناعي تفاعلي\n"
            f"🔢 **الكود:** `{quiz_code}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🚀 اضغط على الزر أدناه لبدء التحدي وقياس مستواك فوراً!"
        )
    
        # إضافة العلامة المائية في نهاية النص إذا كان المستخدم مجانياً
        if watermark:
            announcement_text += f"\n\n✨ تم الإنشاء بواسطة: @TestGenieBot"

        # 2. إنشاء زر الـ Deep Link
        # ملاحظة: استبدل 'YourBotUsername' بيوزر بوتك الحقيقي بدون @
        bot_username = bot.get_me().username
        start_url = f"https://t.me/{bot_username}?start={quiz_code}"
    
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🎯 ابدأ الاختبار الآن", url=start_url))

        # 3. إرسال الرسالة إلى القناة أو المجموعة
        try:
            bot.send_message(
                chat_id=target_chat_id,
                text=announcement_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return True
        except Exception as e:
            print(f"❌ خطأ أثناء النشر في القناة {target_chat_id}: {e}")
            return False


    
    # عند استقبال القناة المختارة
    @bot.message_handler(content_types=['chat_shared'])
    def handle_chat_shared(message):
        user_id = message.from_user.id
        chat_id_to_publish = message.chat_shared.chat_id # القناة المختارة
    
        # 1. استرجاع الكويز الذي كان المستخدم يعمل عليه
        quiz_code = get_user_current_selection(user_id) 
    
        if not quiz_code:
            bot.send_message(message.chat.id, "❌ حدث خطأ، لم نجد الاختبار المطلوب. حاول مرة أخرى.")
            return

        # 2. التحقق: هل المستخدم مشترك (Paid) أم مجاني؟
        if is_paid_user_active(user_id):
            # المستخدم برو: نعطيه خيار "كيف تريد النشر؟" لأننا نحترم وقته
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("📊 استطلاعات مباشرة (Native)", callback_data=f"pub_native_{quiz_code}_{chat_id_to_publish}"))
            keyboard.add(types.InlineKeyboardButton("🔗 رابط تفاعلي (Interactive)", callback_data=f"pub_link_{quiz_code}_{chat_id_to_publish}"))
        
            bot.send_message(message.chat.id, "✨ أنت مستخدم Pro! كيف تريد ظهور الاختبار في قناتك؟", reply_markup=keyboard)
        else:
            # المستخدم مجاني: ننشر فوراً بـ "الطريقة التفاعلية" (التي تفيدك أنت)
            publish_interactive_link(bot, chat_id_to_publish, quiz_code, watermark=True)
        
            # رسالة نجاح في شات البوت الخاص
            bot.send_message(message.chat.id, "✅ تم نشر الاختبار في قناتك بنجاح باستخدام الرابط التفاعلي!")
        
            # تلميح للترقية (Soft Sell)
            bot.send_message(message.chat.id, "💡 هل تعلم؟ يمكنك نشر الاختبار كـ استطلاعات (Polls) مباشرة بدون روابط عند الاشتراك في البرو.")








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
