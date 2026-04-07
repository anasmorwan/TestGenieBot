class QuizQuestion:

    def __init__(self, question, options, correct_index, branch="", explanation=""):
        self.question = question
        self.options = options
        self.correct_index = correct_index
        self.explanation = explanation
        self.branch = branch
    # دالة التحويل لقاموس (للحفظ في القاعدة)
    def to_dict(self):
        return {
            "question": self.question,
            "options": self.options,
            "correct_index": self.correct_index,
            "explanation": self.explanation,
            "branch": self.branch
        }

    
    @classmethod
    def from_raw(cls, q):
        if isinstance(q, dict):
            return cls(
                question=q.get("question"),
                options=q.get("options"),
                correct_index=q.get("correct_index"),
                branch=q.get("branch", ""),
                explanation=q.get("explanation", "")
            )

        if isinstance(q, (list, tuple)):
            return cls(
                question=q[0],
                options=q[1],
                correct_index=q[2],
                branch=q[3] if len(q) > 3 else "",
                explanation=q[4] if len(q) > 4 else ""
            )

        return None
