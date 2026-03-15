# bot/handlers/payment_handler.py

def register(bot):

    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):

        user_id = message.from_user.id

        payload = message.successful_payment.invoice_payload

        if payload == "user_premium_subscription":
            # تحديث قاعدة البيانات
            activate_premium(user_id)

        bot.send_message(
            message.chat.id,
            "Subscription activated successfully."
        )
