from telebot import types
from services.usage import is_paid_user_active
from storage.quiz_repository import get_user_current_selection

def register(bot):
    
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
