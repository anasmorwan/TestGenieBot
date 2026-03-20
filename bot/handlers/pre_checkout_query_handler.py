# bot/handlers/payment_handler.py
from services.usage import activate_subscription



def register_payment(bot):
    # الخطوة 1: الموافقة على طلب الدفع (إلزامي)
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        activate_subscription(user_id, "pro")
        
