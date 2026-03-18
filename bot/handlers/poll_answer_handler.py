
def register(bot):
    
    @bot.poll_answer_handler()
    def handle_poll_answer(poll_answer):
        print("POLL ANSWER RECEIVED:", poll_answer)

        user_id = poll_answer.user.id
        chat_id = quiz_manager.poll_map.get(poll_answer.poll_id)
        selected_option = poll_answer.option_ids[0] if poll_answer.option_ids else None

        # 👇 هنا تنادي الانتقال للسؤال التالي
        quiz_manager.handle_answer(user_id, selected_option, bot)
