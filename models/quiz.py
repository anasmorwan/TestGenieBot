class QuizQuestion:

    def __init__(self, question, options, correct_index, branch="", explanation="", expert_tip=""):
        self.question = question
        self.options = options
        self.correct_index = correct_index
        self.explanation = explanation
        self.branch = branch
        self.expert_tip = expert_tip  # المفتاح الجديد

    # دالة التحويل لقاموس (للحفظ في القاعدة)
    def to_dict(self):
        return {
            "question": self.question,
            "options": self.options,
            "correct_index": self.correct_index,
            "explanation": self.explanation,
            "branch": self.branch,
            "expert_tip": self.expert_tip  # إضافته هنا
        }

    @classmethod
    def from_raw(cls, q):
        if isinstance(q, dict):
            return cls(
                question=q.get("question"),
                options=q.get("options"),
                correct_index=q.get("correct_index"),
                branch=q.get("branch", ""),
                explanation=q.get("explanation", ""),
                expert_tip=q.get("expert_tip", "")  # إضافته مع قيمة افتراضية
            )

        if isinstance(q, (list, tuple)):
            # الخيار السادس (index 5) هو expert_tip
            return cls(
                question=q[0],
                options=q[1],
                correct_index=q[2],
                branch=q[3] if len(q) > 3 else "",
                explanation=q[4] if len(q) > 4 else "",
                expert_tip=q[5] if len(q) > 5 else ""  # إضافته
            )

        return None
