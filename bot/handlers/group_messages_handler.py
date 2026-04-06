
from models.pattern_detection import detect_quiz_pattern # استيراد الدالة الأساسية من كودك
from services.user_trap import update_last_active

def register(bot):
    @bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'], content_types=["text"])
    def handle_group_messages(message):
        print(f"📥 [New Message] From: {message.from_user.username} in Chat: {message.chat.id}", flush=True)
        
        chat_id = message.chat.id
        user_name = message.from_user.first_name
        user_id = message.from_user.id
        update_last_active(user_id)
            
        
        text = message.text or message.caption
        if not text:
            print("❌ [Skip] Message has no text or caption.", flush=True)
            return

        print(f"📝 [Processing] Text Length: {len(text)} characters.", flush=True)

        # محاولة تشغيل المحرك
        try:
            # تنبيه: إذا كان النص يحتوي على أسئلة كثيرة، يفضل معالجته سطراً بسطر 
            # أو إرساله كما هو للمحرك وتخفيض العتبة مؤقتاً للفحص
            result = detect_quiz_pattern(text)
            
            if not result:
                print("⚠️ [Pattern] No quiz pattern detected by the engine (Score too low or invalid structure).", flush=True)
                # فحص سريع لطباعة النتيجة حتى لو فشلت (لأغراض التصحيح)
                return

            confidence = result.get("confidence", 0)
            decision = result.get("decision", "review")
            
            print(f"🎯 [Match Found] Question: {result['question'][:30]}... | Confidence: {confidence}", flush=True)


            if not result.get("is_quiz", False):
                print("⚠️ [Pattern] Result returned but not confident enough.", flush=True)
                return

                
            if confidence >= 0.70: # خفضناها قليلاً للتجربة
                
                response_text = (
                    f"✅ **تم اكتشاف سؤال جديد!**\n"
                    f"📊 درجة الثقة: {confidence:.2f}\n"
                    f"❓ **السؤال:** {result['question']}\n"
                    f"📝 **الخيارات:**\n" + 
                    "\n".join([f"- {opt}" for opt in result['options']])
                )

                # إرسال للأدمن
                print(f"🔗 [Action] Sending to admins of chat {chat_id}", flush=True)
                admins = bot.get_chat_administrators(chat_id)
                sent_count = 0
                for admin in admins:
                    if not admin.user.is_bot:
                        try:
                            bot.send_message(admin.user.id, response_text, parse_mode="Markdown")
                            sent_count += 1
                            
                
                        except Exception as e:
                            print(f"❌ [Error] Could not send to admin {admin.user.id}: {e}", flush=True)
                
                print(f"✅ [Done] Sent to {sent_count} admins.", flush=True)

            
            if decision == "accept":
                admins = bot.get_chat_administrators(chat_id)
                sent_count = 0
                for admin in admins:
                    if not admin.user.is_bot:
                        bot.send_message(chat_id=admin.user.id, text="تم اعتماد السؤال", parse_mode="Markdown")

            
            elif decision == "review":
                admins = bot.get_chat_administrators(chat_id)
                sent_count = 0
                for admin in admins:
                    if not admin.user.is_bot:
                
                         bot.send_message(chat_id=admin.user.id, text="السؤال يحتاج مراجعة", parse_mode="Markdown")

        
        except Exception as e:
            print(f"🔥 [Critical Error] Inside Handler: {e}", flush=True)
            import traceback
            traceback.print_exc()


    
            
