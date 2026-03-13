def store_quiz(user_id, quizzes):

    conn = sqlite3.connect("quiz_users.db")
    c = conn.cursor()

    quiz_code = generate_unique_quiz_code()

    c.execute(
        "INSERT INTO user_quizzes (user_id, quiz_data, quiz_code) VALUES (?, ?, ?)",
        (user_id, json.dumps(quizzes), quiz_code)
    )

    conn.commit()
    conn.close()

    return quiz_code
