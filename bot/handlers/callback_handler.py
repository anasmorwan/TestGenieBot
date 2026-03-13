# bot/handlers/callback_handler.py

from services.quiz_session_service import quiz_manager

def register(bot):

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):

        data = call.data
        quiz_code = data.split(":")[1]
        chat_id = call.message.chat.id

        if data.startswith("start_quiz"):
            quiz_manager.start_quiz(chat_id, quiz_code, bot)

        elif data == "post_quiz":
            bot.send_message(chat_id, "ميزة نشر الاختبار قريباً")


