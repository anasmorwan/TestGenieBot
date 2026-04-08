from services.quiz_session_service import quiz_manager
from services.user_trap import update_last_active

def register(bot):
    
    @bot.poll_answer_handler()
    def handle_poll_answer(poll_answer):
        user_id = poll_answer.user.id
        update_last_active(user_id)
    
        with quiz_manager.lock:
            poll_data = quiz_manager.poll_map.get(poll_answer.poll_id)
        
            # ✅ تحقق من وجود البيانات أولاً
            if poll_data is None:
                print(f"⚠️ Poll ID {poll_answer.poll_id} not found in map!")
                return
        
            chat_id = poll_data.get("chat_id")
            only_mistakes = poll_data.get("only_mistakes")
        
            # ✅ تحقق من القيم
            if chat_id is None:
                print(f"⚠️ chat_id missing for poll {poll_answer.poll_id}")
                return
    
        print("RESOLVED CHAT ID:", chat_id)
        print("ONLY MISTAKES:", only_mistakes)
        selected_option = poll_answer.option_ids[0] if poll_answer.option_ids else None
        # 👇 هنا تنادي الانتقال للسؤال التالي
        quiz_manager.handle_answer(chat_id, selected_option, bot, only_mistakes)


