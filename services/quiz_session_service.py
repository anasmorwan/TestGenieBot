import sqlite3
import json
from datetime import datetime
from models.quiz import QuizQuestion
from services.poll_service import send_question
import threading

class QuizManager:

    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()


    def start_quiz(self, chat_id, quiz_code, bot):

        quiz_data = self.load_quiz(quiz_code)
        if not quiz_data:
            return False

        questions = []
        for q in quiz_data:
            obj = QuizQuestion.from_raw(q)
            if obj:
                questions.append(obj)

        if not questions:
            return False

        with self.lock:
            self.sessions[chat_id] = {
            "questions": questions,
            "index": 0,
            "score": 0,
            "quiz_code": quiz_code
        }

        
        with self.lock:
            self.send_current_question(chat_id, bot)

        return True

        def load_quiz(self, quiz_code):
            with self.lock:
                conn = sqlite3.connect("quiz_users.db")
                c = conn.cursor()

                c.execute(
                    "SELECT quiz_data FROM user_quizzes WHERE quiz_code=?",
                    (quiz_code,)
                )

                row = c.fetchone()
                conn.close()

                if not row:
                    return None

                return json.loads(row[0])
    

    def send_current_question(self, chat_id, bot):
        with self.lock:
            state = self.sessions.get(chat_id)

        if not state:
            return

        q = state["questions"][state["index"]]

        send_question(bot, chat_id, q)

    def handle_answer(self, poll_answer, bot):

        chat_id = poll_answer.user.id

        with self.lock:
            state = self.sessions.get(chat_id)
        if not state:
            return

        q = state["questions"][state["index"]]

        if poll_answer.option_ids[0] == q.correct_index:
            state["score"] += 1

        state["index"] += 1

        if state["index"] >= len(state["questions"]):
            self.finish_quiz(chat_id, bot)
        else:
            self.send_current_question(chat_id, bot)

    def finish_quiz(self, chat_id, bot):
        
        with self.lock:
            state = self.sessions.pop(chat_id, None)
        if not state:
            return

        score = state["score"]
        total = len(state["questions"])

        bot.send_message(
            chat_id,
            f"انتهى الاختبار\n\nالنتيجة: {score}/{total}"
        )
