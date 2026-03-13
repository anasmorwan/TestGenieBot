class QuizSessionManager:

    def __init__(self):
        self.active_sessions = {}

    def start_session(self, chat_id, quizzes):

        self.active_sessions[chat_id] = {
            "quizzes": quizzes,
            "index": 0,
            "score": 0
        }

    def get_current_question(self, chat_id):

        state = self.active_sessions.get(chat_id)

        if not state:
            return None

        return state["quizzes"][state["index"]]
