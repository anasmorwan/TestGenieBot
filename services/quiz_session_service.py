import sqlite3
from storage.sqlite_db import get_connection
import json
from datetime import datetime
from models.quiz import QuizQuestion
# from services.poll_service import send_quiz_poll
import threading


 
class QuizManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        
        # ✅ هذا هو الناقص
        self.poll_map = {}

    def start_quiz(self, chat_id, quiz_code, bot):
        print("QUIZ CODE:", quiz_code, flush=True)
        quiz_data = self.load_quiz(quiz_code)
        print("LOADED QUIZ:", quiz_data, flush=True)
        if not quiz_data:
            print("❌ No quiz data", flush=True)
            return False

    
        questions = []
        for q in quiz_data:
            obj = QuizQuestion.from_raw(q)
            print("RAW:", q, flush=True)
            print("PARSED:", obj, flush=True)
            if obj:
                questions.append(obj)

        
        print("TOTAL QUESTIONS:", len(questions))

        if not questions:
            print("❌ No questions", flush=True)
            return False
        
        
        with self.lock:
            self.sessions[chat_id] = {
            "questions": questions,
            "index": 0,
            "score": 0,
            "quiz_code": quiz_code
        }

        
        
        self.send_current_question(chat_id, bot)

        return True

    def load_quiz(self, quiz_code):
        with self.lock:
            conn = get_connection()
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
            print("No quiz session found for chat:", chat_id)
            return

        if state["index"] >= len(state["questions"]):
            print("Index out of range for chat:", chat_id)
            return


        q = state["questions"][state["index"]]
        print(f"Sending question {state['index']+1} to chat {chat_id}")

        self.send_quiz_poll(bot, chat_id, q)

    def handle_answer(self, poll_answer, bot):

        chat_id = poll_answer.user.id

        
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
        
        
        state = self.sessions.pop(chat_id, None)
        if not state:
            return

        score = state["score"]
        total = len(state["questions"])

        bot.send_message(
            chat_id,
            f"انتهى الاختبار\n\nالنتيجة: {score}/{total}"
        )

    
    def send_quiz_poll(self, bot, chat_id, question):
        try:
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

            self.poll_map[poll.poll.id] = chat_id

            return poll.message_id

        except Exception:
            import logging
            logging.exception("SEND POLL FAILED")
            return None



quiz_manager = QuizManager()
