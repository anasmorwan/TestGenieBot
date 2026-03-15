# bot/handlers/payment_handler.py

def register_payment(bot):
    # الخطوة 1: الموافقة على طلب الدفع (إلزامي)
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    # الخطوة 2: ماذا يحدث بعد نجاح الدفع؟
    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        # هنا يمكنك تحديث قاعدة البيانات للمستخدم
        # message.successful_payment.invoice_payload سيعطيك "user_premium_subscription"
        bot.send_message(message.chat.id, "شكراً لك! تم تفعيل الاشتراك بنجاح 🌟")
