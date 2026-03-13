class QuizQuestion:

    def __init__(self, question, options, correct_index, explanation=""):
        self.question = question
        self.options = options
        self.correct_index = correct_index
        self.explanation = explanation

    @classmethod
    def from_raw(cls, q):

        if isinstance(q, dict):
            return cls(
                q.get("question"),
                q.get("options"),
                q.get("correct_index"),
                q.get("explanation", "")
            )

        if isinstance(q, (list, tuple)):
            return cls(q[0], q[1], q[2], q[3] if len(q) > 3 else "")

        return None
