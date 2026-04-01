import telebot
from quiz_detector import detect_quiz_pattern # استيراد الدالة الأساسية من كودك

# ضع توكن البوت الخاص بك هنا
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_group_messages(message):
    # 1. التأكد أن الرسالة من مجموعة أو سوبر جروب
    if message.chat.type not in ['group', 'supergroup']:
        return

    text = message.text or message.caption
    if not text:
        return

    # 2. تشغيل المحرك الذكي الخاص بك
    result = detect_quiz_pattern(text)

    # 3. إذا كانت النتيجة "سؤال" وبثقة أعلى من العتبة المحددة
    if result:
        # استخراج بيانات الأدمن (اختياري: يمكنك إرسالها لشخص محدد بـ ID ثابت)
        chat_id = message.chat.id
        user_name = message.from_user.first_name
        
        # تنسيق الإجابة لإرسالها للآدمن
        response_text = (
            f"✅ **تم اكتشاف سؤال جديد!**\n"
            f"👤 بواسطة: {user_name}\n"
            f"📊 درجة الثقة: {result.get('score', 0):.2f}\n"
            f"--- \n"
            f"❓ **السؤال:** {result['question']}\n"
            f"📝 **الخيارات:**\n" + 
            "\n".join([f"- {opt}" for opt in result['options']])
        )

        # إرسال النتيجة للأدمن (هنا نرسلها لنفس الشات كمثال، أو يمكنك وضع ID ثابت)
        # لإرسالها للآدمن الخاص بالمجموعة برمجياً:
        try:
            admins = bot.get_chat_administrators(chat_id)
            for admin in admins:
                if not admin.user.is_bot:
                    bot.send_message(admin.user.id, response_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending to admin: {e}")
            # fallback: إرسال رد في المجموعة إذا فشل الإرسال الخاص
            bot.reply_to(message, "تم رصد سؤال اختبار وإبلاغ الإدارة.")

print("Bot is running...")
bot.infinity_polling()
