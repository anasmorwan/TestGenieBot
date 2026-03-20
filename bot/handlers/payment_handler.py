# bot/handlers/payment_handler.py

def register(bot):

    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        user_id = message.from_user.id
        payload = message.successful_payment.invoice_payload

        if payload == "pro_plan":
            activate_subscription(user_id, "pro")

        elif payload == "pro_plus_plan":
            activate_subscription(user_id, "pro_plus")

        bot.send_message(
            message.chat.id,
            "Subscription activated successfully."
        )
