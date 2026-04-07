# storage/sqlite_db.py

import sqlite3
import json
from datetime import datetime, timedelta
DB_PATH = "quiz_users.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False, timeout=20)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        last_text TEXT,
        specialty TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_id ON user_knowledge(user_id)")
    # أضف هذا السطر لتصحيح القاعدة (شغله مرة واحدة)
    cursor.execute("DROP INDEX IF EXISTS idx_user_id")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_mistakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_text TEXT,
        options TEXT, -- JSON string
        correct_index INTEGER,
        explanation TEXT,
        fail_count INTEGER DEFAULT 1,
        correct_count INTEGER DEFAULT 0,
        last_failed TEXT
    )
    """)
    
    

    # جدول لتخزين نقاط التخصصات لكل مستخدم
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_interests (
        user_id INTEGER,
        domain_name TEXT,
        points INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, domain_name),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users_trap (
        user_id INTEGER PRIMARY KEY,
        level TEXT DEFAULT 'beginner',
        specialization TEXT,
        last_topic TEXT,
        xp INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        last_quiz_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    correct_answers INTEGER,
    total_questions INTEGER,
    quiz_type TEXT,  -- daily / normal
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        major TEXT,
        native_lang TEXT DEFAULT 'ar',
        quiz_count INTEGER DEFAULT 0,
        last_reset TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        plan TEXT DEFAULT 'free',
        expires_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        rewarded INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        quiz_data TEXT NOT NULL,
        quiz_code TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1
    )
    """)
    

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_shares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_code TEXT NOT NULL,
        shared_by_user_id INTEGER NOT NULL,
        shared_by_name TEXT,
        shared_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,      -- صاحب الحساب
        channel_id INTEGER NOT NULL,   -- Chat ID الخاص بالقناة
        channel_name TEXT,             -- اسم القناة للعرض على الزر
        channel_type TEXT,             -- 'channel' أو 'group'
        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, channel_id)    -- لمنع التكرار لنفس المستخدم
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sample_quizzes (
        quiz_code TEXT PRIMARY KEY,
        quiz_data TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    try:

        # أضف العمود الجديد في أمر منفصل
        cursor.execute("ALTER TABLE users ADD COLUMN free_quizzes INTEGER DEFAULT 3;")
        cursor.execute("ALTER TABLE users ADD COLUMN invited_by INTEGER;")
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
        cursor.execute("ALTER TABLE users ADD COLUMN used_today DEFAULT 0;")
        cursor.execute("ALTER TABLE users ADD COLUMN daily_limit DEFAULT 3;")
        # فحص وجود العمود في جدول users
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
    
        if "current_quiz_selection" not in columns:
            print("⚠️ عمود current_quiz_selection مفقود، جاري الإضافة...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN current_quiz_selection TEXT DEFAULT 'sample_quiz';")
                conn.commit()
                print("✅ تم إضافة العمود بنجاح.")
            except Exception as e:
                print(f"❌ خطأ أثناء إضافة العمود: {e}")
            

        cursor.execute("ALTER TABLE subscriptions ADD COLUMN daily_quiz_limit INTEGER DEFAULT 3;")
        cursor.execute("ALTER TABLE subscriptions ADD COLUMN daily_ocr_limit INTEGER DEFAULT 1;")
        
        
    
        print("✅ تم إضافة عمود daily_ocr_limit بنجاح.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ العمود موجود بالفعل، تم تخطي التعديل.")
        else:
            print(f"❌ خطأ غير متوقع: {e}")
            
    
    
    conn.commit()
    conn.close()
    
#--------------------------
#    🔹 دوال data-driven messages 
#--------------------------
def get_top_mistake(cursor, user_id):
    cursor.execute("""
        SELECT question_text, fail_count, correct_count
        FROM user_mistakes
        WHERE user_id = ?
        ORDER BY fail_count DESC
        LIMIT 1
    """, (user_id,))
    
    return cursor.fetchone()

def get_top_interest(cursor, user_id):
    cursor.execute("""
        SELECT domain_name, points
        FROM user_interests
        WHERE user_id = ?
        ORDER BY points DESC
        LIMIT 1
    """, (user_id,))
    
    return cursor.fetchone()

def get_top_interest(cursor, user_id):
    cursor.execute("""
        SELECT domain_name, points
        FROM user_interests
        WHERE user_id = ?
        ORDER BY points DESC
        LIMIT 1
    """, (user_id,))
    
    return cursor.fetchone()

def get_last_learning(cursor, user_id):
    cursor.execute("""
        SELECT specialty, updated_at
        FROM user_knowledge
        WHERE user_id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    
    if not row:
        return None
    
    specialty, updated_at = row
    return {
        "specialty": specialty,
        "updated_at": updated_at
    }

def get_user_profile(cursor, user_id):
    cursor.execute("""
        SELECT xp, streak, level, last_topic
        FROM users_trap
        WHERE user_id = ?
    """, (user_id,))
    
    return cursor.fetchone()

def build_dynamic_message(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    profile = get_user_profile(cursor, user_id)
    mistake = get_top_mistake(cursor, user_id)
    interest = get_top_interest(cursor, user_id)
    learning = get_last_learning(cursor, user_id)

    xp, streak, level, last_topic = profile if profile else (0, 0, "beginner", None)
    
    if profile is not None and mistake is not None and interest is not None and learning is not None:
        parts = []

        # 1) Hook
        if streak > 5:
            parts.append(f"🔥 سلسلة قوية: {streak} أيام!")
        else:
            parts.append("🔥 جاهز لتحدي جديد؟")

        # 2) الاهتمامات
        if interest:
            domain, points = interest
            parts.append(f"📚 واضح أنك مهتم بـ {domain}")

        # 3) آخر تعلم (المهم)
        if learning and learning.get("specialty"):
            parts.append(f"🧠 آخر مراجعة كانت عن {learning['specialty']}")

        # 4) الأخطاء
        if mistake:
            q_text, fails, corrects = mistake
            parts.append(f"⚠️ عندك نقطة تتكرر ({fails} مرات)... جاهز تحلها؟")

        # 5) CTA دائمًا موجود
        parts.append("👇 ابدأ الآن واختبر نفسك")

        return "\n\n".join(parts)
    else:
        return False   
#--------------------------
#    🔹 دوال الادمن المساعدة
#--------------------------

def get_user_knowledge(user_id):
    """جلب جميع النصوص المحفوظة لمستخدم معين"""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        c.execute("""
            SELECT id, last_text, specialty, updated_at
            FROM user_knowledge 
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
        
        rows = c.fetchall()
        
        knowledge_list = []
        for row in rows:
            knowledge_list.append({
                'id': row[0],
                'last_text': row[1],
                'specialty': row[2],
                'updated_at': row[3]
            })
        
        return knowledge_list
        
    except Exception as e:
        print(f"Error in get_user_knowledge: {e}")
        return []
    finally:
        conn.close()
        

#--------------------------
#    🔹 دوال مساعدة
#--------------------------
def update_user_difficulty(user_id, difficulty):
    """
    تغيير مستوى الصعوبة للمستخدم
    
    Args:
        user_id: معرف المستخدم
        difficulty: مستوى الصعوبة ('early', 'mid', 'advanced')
    
    Returns:
        bool: نجاح العملية أم لا
    """
    conn = get_connection()
    cursor = conn.cursor()
    valid_difficulties = ['early', 'mid', 'advanced']
    
    if difficulty not in valid_difficulties:
        print(f"Invalid difficulty: {difficulty}. Must be one of {valid_difficulties}")
        return False
    
    try:
        # التحقق إذا كان المستخدم موجود
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            # مستخدم جديد: أدخل مع الصعوبة المحددة
            cursor.execute("""
                INSERT INTO user_quizzes (user_id, difficulty) 
                VALUES (?, ?)
            """, (user_id, difficulty))
        else:
            # مستخدم موجود: حدث الصعوبة
            cursor.execute("""
                UPDATE user_quizzes SET difficulty = ? WHERE user_id = ?
            """, (difficulty, user_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error updating difficulty for user {user_id}: {e}")
        return False


def init_user_quiz_count(user_id, default_count):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # التحقق إذا كان المستخدم موجود
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            # مستخدم جديد: أدخل
            cursor.execute("""
                INSERT INTO users (user_id, quiz_num) 
                VALUES (?, ?)
            """, (user_id, default_count))
        else:
            # مستخدم موجود: حدث القيمة دائماً
            cursor.execute("""
                UPDATE users SET quiz_num = ? WHERE user_id = ?
            """, (default_count, user_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()


def get_user_difficulty(user_id):
    """
    استرجاع مستوى الصعوبة للمستخدم
    
    Args:
        user_id: معرف المستخدم
    
    Returns:
        str: مستوى الصعوبة ('early', 'mid', 'advanced') أو 'early' كقيمة افتراضية
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT difficulty FROM user_quizzes WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result and result[0] is not None:
            return result[0]
        else:
            return 'early'  # القيمة الافتراضية
            
    except Exception as e:
        print(f"Error getting difficulty for user {user_id}: {e}")
        return 'early'

def get_user_question_count(user_id):
    """
    استرجاع عدد الأسئلة للمستخدم
    
    Args:
        user_id: معرف المستخدم
    
    Returns:
        int: عدد الأسئلة أو 10 كقيمة افتراضية
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT quiz_num FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result and result[0] is not None:
            return int(result[0])  # تأكد من إرجاع int
        else:
            return 10  # القيمة الافتراضية
            
    except Exception as e:
        print(f"Error getting question count for user {user_id}: {e}")
        return 10  # ✅ في حالة الخطأ، أرجع القيمة الافتراضية أيضاً
    finally:
        conn.close()


#--------------------------
#    🔹 دوال مساعدة user_major
#--------------------------
def update_user_major(user_id, detected_domain):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_interests (user_id, domain_name, points)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, domain_name) 
        DO UPDATE SET points = points + 1
    """, (user_id, detected_domain))
    
    # 2. جلب التخصص الذي يملك أعلى عدد نقاط لهذا المستخدم
    cursor.execute("""
        SELECT domain_name FROM user_interests 
        WHERE user_id = ? 
        ORDER BY points DESC LIMIT 1
    """, (user_id,))
    
    top_major = cursor.fetchone()[0]
    
    # 3. تحديث الجدول الرئيسي للمستخدمين ليعكس التخصص الطاغي
    cursor.execute("UPDATE users SET major = ? WHERE user_id = ?", (top_major, user_id))
    conn.commit()
    

def migrate_users_to_trap():
    conn = get_connection()
    cursor = conn.cursor()
    
    # جلب جميع المستخدمين من الجدول القديم
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    
    count = 0
    for user_row in users:
        user_id = user_row[0]
        
        # إدراج المستخدم في الجدول الجديد إذا لم يكن موجوداً
        cursor.execute("""
            INSERT OR IGNORE INTO users_trap (user_id, xp, streak, last_quiz_date)
            VALUES (?, 0, 0, NULL)
        """, (user_id,))
        
        if cursor.rowcount > 0:
            count += 1
    
    conn.commit()
    print(f"✅ تم نقل {count} مستخدم إلى جدول users_trap")

    



def is_user_exist(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def log_new_user():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (user_id, last_reset) VALUES (?, ?)",
        (user_id, datetime.utcnow().isoformat())
    )
    conn.commit()



def get_user_mistakes_stats(user_id):
    """ترجع إحصائيات الأخطاء للمستخدم"""
    conn = get_connection()
    c = conn.cursor()
    
    # العدد الإجمالي للأخطاء الفريدة (سؤال واحد يحسب مرة)
    c.execute("""
        SELECT COUNT(*) FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0
    """, (user_id,))
    
    total_mistakes = c.fetchone()[0]
    
    # الأخطاء الحديثة (آخر 7 أيام)
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    c.execute("""
        SELECT COUNT(*) FROM user_mistakes 
        WHERE user_id = ? AND last_failed > ?
    """, (user_id, week_ago))
    
    recent_mistakes = c.fetchone()[0]
    
    # متوسط تكرار الخطأ لكل سؤال
    c.execute("""
        SELECT AVG(fail_count) FROM user_mistakes 
        WHERE user_id = ?
    """, (user_id,))
    
    avg_fail = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_mistakes": total_mistakes,
        "recent_mistakes": recent_mistakes,
        "avg_fail_count": round(avg_fail, 2)
    }

def get_user_mistakes_by_age(user_id):
    """ترجع الأخطاء مرتبة حسب القدم (الأقدم أولاً)"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT id, question_text, options, correct_index, explanation, 
               fail_count, last_failed, created_at
        FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0
        ORDER BY created_at ASC
    """, (user_id,))
    
    mistakes = []
    for row in c.fetchall():
        mistakes.append({
            "id": row[0],
            "question_text": row[1],
            "options": json.loads(row[2]),
            "correct_index": row[3],
            "explanation": row[4],
            "fail_count": row[5],
            "last_failed": row[6],
            "created_at": row[7]
        })
    
    conn.close()
    return mistakes

def get_recent_mistakes(user_id, limit=10):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT id, question_text, options, correct_index, explanation, fail_count
        FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0
        ORDER BY last_failed DESC
        LIMIT ?
    """, (user_id, limit))
    
    mistakes = []
    for row in c.fetchall():
        mistakes.append({
            "id": row[0],
            "questions": {
                "question": row[1],
                "options": json.loads(row[2]),
                "correct_index": row[3],
                "explanation": row[4]
            },
            "fail_count": row[5]
        })
    
    conn.close()
    return mistakes  # ترجع قائمة، ويمكن أن تكون فارغة []

def get_question_distribution(user_id, total_questions=10):
    """تحديد نسبة الأسئلة حسب حالة المستخدم"""
    stats = get_user_mistakes_stats(user_id)
    
    mistakes_count = stats["total_mistakes"]
    recent_count = stats["recent_mistakes"]
    
    # تحديد الحالة
    if mistakes_count >= 5:  # أخطاء كثيرة
        # 🟢 الحالة 1: أخطاء كثيرة
        review_percent = 0.40
        new_percent = 0.40
        challenge_percent = 0.20
        
    elif mistakes_count > 0:  # أخطاء قليلة
        # 🟡 الحالة 2: أخطاء قليلة
        review_percent = 0.20
        new_percent = 0.60
        challenge_percent = 0.20
        
    else:  # لا توجد أخطاء
        # 🔴 الحالة 3: لا توجد أخطاء
        review_percent = 0.00
        new_percent = 0.80
        challenge_percent = 0.20
    
    # حساب العدد الفعلي
    review_count = round(total_questions * review_percent)
    new_count = round(total_questions * new_percent)
    challenge_count = total_questions - review_count - new_count
    
    return {
        "status": "many_mistakes" if mistakes_count >= 5 else "few_mistakes" if mistakes_count > 0 else "no_mistakes",
        "review_count": review_count,
        "new_count": new_count,
        "challenge_count": challenge_count,
        "total_mistakes": mistakes_count,
        "recent_mistakes": recent_count
    }


# --------------------------
#----------          -------
#    <🔹 دوال تعديل sqlite >
#-------------------
# --------------------------


def table_exists(table):
    """التحقق من وجود جدول في قاعدة البيانات"""
    conn = get_connection()
    c = conn.cursor()
    
    # التحقق من وجود الجدول
    c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    exists = c.fetchone() is not None
    
    conn.close()
    return exists


def column_exists(table, column):
    conn = get_connection()
    c = conn.cursor()

    c.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in c.fetchall()]

    conn.close()
    return column in columns


def safe_add_column():
    conn = get_connection()
    c = conn.cursor()

    if not column_exists("user_quizzes", "quiz_type"):
        c.execute("""
        ALTER TABLE user_quizzes ADD COLUMN quiz_type TEXT DEFAULT 'standard'
        """)
        
    if not column_exists("users", "current_quiz_selection"):
        c.execute("""
        ALTER TABLE users ADD COLUMN current_quiz_selection TEXT DEFAULT 'sample_quiz'
        """)

    if not column_exists("user_quizzes", "is_paid"):
        c.execute("""
        ALTER TABLE user_quizzes ADD COLUMN is_paid BOOLEAN DEFAULT 0
        """)
        
        
    if not column_exists("user_quizzes", "difficulty"):
        c.execute("""
        ALTER TABLE user_quizzes ADD COLUMN difficulty TEXT DEFAULT 'early'
        """)
    if not column_exists("users", "quiz_num"):
        c.execute("""
        ALTER TABLE users ADD COLUMN quiz_num INTEGER DEFAULT 5
        """)
        

    if not column_exists("user_mistakes", "created_at"):
        c.execute("""
        ALTER TABLE user_mistakes ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP 
        """)
    if not column_exists("users_trap", "last_quiz_time"):
        c.execute("""
        ALTER TABLE users_trap ADD COLUMN last_quiz_time TEXT 
        """)
    

    conn.commit()
    conn.close()
    print("✅ Schema updated safely")




def safe_add_table():
    conn = get_connection()
    c = conn.cursor()
    if table_exists("quiz_attempts"):
        
        c.execute("""
        DROP TABLE quiz_attempts;
        """)
        
    c.execute("""
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_code TEXT,
        user_id INTEGER,
        score INTEGER,
        total INTEGER,
        timestamp TEXT 
    )
    """)

    conn.commit()
    conn.close()

    



