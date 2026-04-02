import sqlite3

def has_previous_poll(user_id):
    """
    Check if the user has previously generated any poll in the system.
    Returns True if at least one poll is found, otherwise False.
    """
    conn = None
    try:
        # الاتصال بقاعدة البيانات باستخدام الدالة المتوفرة لديك
        conn = get_connection()
        cursor = conn.cursor()

        # البحث عن أي سجل للمستخدم يكون فيه نوع الكويز 'poll'
        # ملاحظة: تم استخدام LIMIT 1 لتحسين الأداء لأننا نحتاج فقط لمعرفة الوجود
        query = """
            SELECT 1 
            FROM user_quizzes 
            WHERE user_id = ? AND quiz_type = 'poll' 
            LIMIT 1
        """
        
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        # إذا وجدنا نتيجة، فهذا يعني أن المستخدم لديه سجل سابق
        return result is not None

    except Exception as e:
        print(f"Error checking for previous poll: {e}")
        return False
    finally:
        if conn:
            conn.close()

# مثال على كيفية استخدام الدالة في منطق البوت الخاص بك:
# if not has_previous_poll(user_id):
#     # أظهر نصيحة تعليمية عبر answerCallbackQuery
#     bot.answer_callback_query(callback_query_id, text="💡 نصيحة: يمكنك إرسال سؤالك مباشرة وسأقوم بتوليد الخيارات لك!", show_alert=True)

