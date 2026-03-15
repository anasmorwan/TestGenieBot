# bot/handlers/callback_handler.py

from services.quiz_session_service import quiz_manager
from storage.session_store import user_state

def register(bot):

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):

        data = call.data
        quiz_code = data.split(":")[1]
        chat_id = call.message.chat.id
        user_id = call.from_user.id


        if data.startswith("start_quiz"):
            quiz_manager.start_quiz(chat_id, quiz_code, bot)

        elif data == "post_quiz":
            bot.send_message(chat_id, "ميزة نشر الاختبار قريباً")

        elif data == "go_generate":
            user_state[user_id] = "awating_test"
            


        elif data.startswith("quick_quiz"):
            quiz_manager.start_quiz(chat_id, quiz_code, bot)

        elif data == "go_account_settings":
            

