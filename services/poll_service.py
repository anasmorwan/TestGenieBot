

def send_quiz_poll(bot, chat_id, question):
    try:
        if question.correct_index >= len(question.options):
            print("Invalid correct index")
            return
        poll = bot.send_poll(
            chat_id=chat_id,
            question=str(question.question)[:300],
            options=[str(opt) for opt in question.options if opt],
            type="quiz",
            correct_option_id=int(question.correct_index),
            explanation=str(question.explanation or "")[:200],
            is_anonymous=False,
            open_period=30
        )
        

        # خزّن الربط
        self.poll_map[poll.poll.id] = chat_id
        return poll.message_id

    except Exception as e:
        import logging
        logging.exception("SEND POLL FAILED")
        print("FAILED DATA:", question.__dict__)
        return None
