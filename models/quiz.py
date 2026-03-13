class QuizQuestion:

    def __init__(self, question, options, correct_index, explanation=""):
        self.question = question
        self.options = options
        self.correct_index = correct_index
        self.explanation = explanation

    def to_dict(self):
        return {
            "question": self.question,
            "options": self.options,
            "correct_index": self.correct_index,
            "explanation": self.explanation
        }
