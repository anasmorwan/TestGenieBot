    # الخطوة 2: ماذا يحدث بعد نجاح الدفع؟
    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        # هنا يمكنك تحديث قاعدة البيانات للمستخدم
        # message.successful_payment.invoice_payload سيعطيك "user_premium_subscription"
        bot.send_message(message.chat.id, "شكراً لك! تم تفعيل الاشتراك بنجاح 🌟")
