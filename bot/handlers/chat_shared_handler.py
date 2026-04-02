from telebot import types
from services.usage import is_paid_user_active
from storage.quiz_repository import get_user_current_quiz
from storage.messages import get_message
from storage.session_store import user_states, get_state_safe






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



        try:
            chat_details = bot.get_chat(chat_id_to_publish)
            chat_title = chat_details.title
        
            state = get_state_safe(user_id)


            if state == "poll":
                receive_text = get_message("POLL_TEXT")

                # حفظ الحالة مع سياق اسم القناة
                user_states[user_id] = {
                "state": "generate_poll",
                "chat_title": chat_title,
                "chat_id": chat_id_to_publish
                }
                bot.send_message(chat_id, receive_text)
                return
                

            else:
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
                     #bot.send_message(message.chat.id, text=get_message("SHARED_QUIZ_REACTIONS"))


                       
        except Exception as e:
            bot.send_message(message.chat.id, f"😴 عذراً، لا يمكنني الوصول لبيانات هذه المجموعة. تأكد أنني عضو فيها.\n\n {str(e)}")
            
        
        
            
