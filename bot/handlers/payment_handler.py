# bot/handlers/payment_handler.py
from services.usage import activate_subscription
from services.backup_service import safe_backup, backup_all
from services.user_trap import update_last_active

def register(bot):

    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        user_id = message.from_user.id
        update_last_active(user_id)
        payload = message.successful_payment.invoice_payload

        if payload == "pro_plan":
            activate_subscription(user_id, "pro")
            backup_all()
            safe_backup(bot)

        elif payload == "pro_plus_plan":
            activate_subscription(user_id, "pro_plus")
            backup_all()
            safe_backup(bot)

        bot.send_message(
            message.chat.id,
            "Subscription activated successfully."
        )
