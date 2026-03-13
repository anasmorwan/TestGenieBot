from bot.bot_instance import bot


def send_question(bot, chat_id, question):

    poll = bot.send_poll(
        chat_id=chat_id,
        question=question.question,
        options=question.options,
        type="quiz",
        correct_option_id=question.correct_index,
        explanation=question.explanation,
        is_anonymous=False,
        open_period=30
    )

    return poll.message_id
