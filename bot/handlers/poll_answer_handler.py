from services.quiz_session_service import quiz_manager
from services.user_trap import update_last_active

def register(bot):
    
    @bot.poll_answer_handler()
    def handle_poll_answer(poll_answer):
        print("POLL ANSWER RECEIVED:", poll_answer)
        
        user_id = poll_answer.user.id
        update_last_active(user_id)
        with quiz_manager.lock:
            chat_id = quiz_manager.poll_map.get(poll_answer.poll_id)
        print("RESOLVED CHAT ID:", chat_id)
        print("POLL MAP:", quiz_manager.poll_map)
        selected_option = poll_answer.option_ids[0] if poll_answer.option_ids else None

        # 👇 هنا تنادي الانتقال للسؤال التالي
        quiz_manager.handle_answer(chat_id, selected_option, bot)
