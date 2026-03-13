from bot.bot_instance import bot


def send_question(chat_id, quiz):

    poll = bot.send_poll(
        chat_id=chat_id,
        question=quiz["question"],
        options=quiz["options"],
        type="quiz",
        correct_option_id=quiz["correct_index"],
        explanation=quiz.get("explanation", ""),
        is_anonymous=False,
        open_period=30
    )

    return poll.message_id
