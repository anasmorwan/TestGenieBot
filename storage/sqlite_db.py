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
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_hash TEXT UNIQUE NOT NULL,
        quiz_data TEXT NOT NULL,
        created_at TEXT NOT NULL
)
""")

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

def get_last_branches(cursor, user_id):
    cursor.execute("""
        SELECT branch
        FROM user_mistakes
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 2
    """, (user_id,))
    
    return cursor.fetchall()  # تعيد قائمة


def get_top_interest(cursor, user_id):
    cursor.execute("""
        SELECT domain_name, points
        FROM user_interests
        WHERE user_id = ?
        ORDER BY points DESC
        LIMIT 1
    """, (user_id,))
    
    return cursor.fetchone()

# def get_last_learning(cursor, user_id):
 #   cursor.execute("""
  #      SELECT specialty, updated_at
  #      FROM user_knowledge
  #      WHERE user_id = ?
 #   """, (user_id,))
    
  #  row = cursor.fetchone()
    
#    if not row:
   #     return None
    
  #  specialty, updated_at = row
  #  return {
     #   "specialty": specialty,
    #    "updated_at": updated_at
  #  }

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
    # learning = get_last_learning(cursor, user_id)
    branches = get_last_branches(cursor, user_id)

    # استخراج القيم الحقيقية فقط
    clean_branches = [b[0] for b in branches if b[0]]
    

    xp, streak, level, last_topic = profile if profile else (0, 0, "beginner", None)
    
    if profile is not None and mistake is not None and interest is not None:
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
        if clean_branches:
            first_branch = clean_branches[0]
            if len(clean_branches) > 1:
                second_branch = clean_branches[1]
            parts.append(f"🧠 آخر مراجعة كانت عن الـ{first_branch}")
    
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
#    🔹حفظ تاريخ الأسئلة
#--------------------------

def save_quiz_attempt(user_id, correct_answers, total_questions):

    conn = get_connection()  # اسم قاعدة البيانات
    cursor = conn.cursor()
    
    # إدراج البيانات الجديدة
    cursor.execute("""
        INSERT INTO quiz_history (user_id, correct_answers, total_questions, quiz_type)
        VALUES (?, ?, ?, 'normal')
    """, (user_id, correct_answers, total_questions))
    
    conn.commit()
    conn.close()
    
    print(f"✅ تم حفظ المحاولة: {correct_answers}/{total_questions} إجابة صحيحة")


def get_normal_questions_total(user_id):
    """
    إرجاع عدد الأسئلة من الاختبارات العادية فقط (normal)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT SUM(total_questions) as total
        FROM quiz_history
        WHERE user_id = ? AND quiz_type = 'normal'
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    total = result[0] if result[0] is not None else 0
    print(f"📊 المستخدم {user_id} أجاب على {total} سؤال في الاختبارات العادية")
    return total

def get_total_questions(user_id):
    """
    إرجاع عدد جميع الأسئلة التي أجاب عليها المستخدم (من كل المحاولات)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT SUM(total_questions) as total
        FROM quiz_history
        WHERE user_id = ?
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    total = result[0] if result[0] is not None else 0
    print(f"📊 المستخدم {user_id} أجاب على {total} سؤال في المجمل")
    return total



def get_today_attempts(user_id):
    """
    إرجاع جميع محاولات المستخدم التي تم حفظها اليوم
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # الحصول على تاريخ اليوم بصيغة YYYY-MM-DD
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    # استعلام لجلب محاولات اليوم فقط
    cursor.execute("""
        SELECT id, user_id, correct_answers, total_questions, quiz_type, created_at
        FROM quiz_history
        WHERE user_id = ? AND DATE(created_at) = ?
        ORDER BY created_at DESC
    """, (user_id, today_date))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print(f"📅 لا توجد محاولات للمستخدم {user_id} اليوم")
        return []
    
    print(f"📅 محاولات المستخدم {user_id} اليوم ({today_date}):")
    print("-" * 60)
    
    attempts = []
    for row in results:
        attempt = {
            'id': row[0],
            'user_id': row[1],
            'correct_answers': row[2],
            'total_questions': row[3],
            'quiz_type': row[4],
            'created_at': row[5]
        }
        attempts.append(attempt)
        
        print(f"  🎯 {attempt['quiz_type']}: {attempt['correct_answers']}/{attempt['total_questions']} - {attempt['created_at']}")
    
    return attempts


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
#    🔹 دوال مساعدة (الصعوبة و عدد الاختبارات)
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
    """
    تهيئة أو تحديث عدد الاختبارات للمستخدم
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # التحقق إذا كان المستخدم موجود
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            # مستخدم جديد
            cursor.execute("""
                INSERT INTO users (user_id, quiz_num) 
                VALUES (?, ?)
            """, (user_id, default_count))
            print(f"✅ New user {user_id}: quiz_num set to {default_count}")
        else:
            # مستخدم موجود: حدث القيمة دائماً
            cursor.execute("""
                UPDATE users SET quiz_num = ? WHERE user_id = ?
            """, (default_count, user_id))
            print(f"✅ Updated user {user_id}: quiz_num = {default_count}")
        
        conn.commit()
        
        # تحقق من أن القيمة حفظت
        cursor.execute("SELECT quiz_num FROM users WHERE user_id = ?", (user_id,))
        saved = cursor.fetchone()
        print(f"Verification: quiz_num = {saved[0] if saved else 'None'}")
        
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
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # طباعة اسم الجدول والأعمدة الموجودة
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print(f"Columns in users table: {[col[1] for col in columns]}", flush=True)
        
        # استعلام القيمة
        cursor.execute("SELECT quiz_num FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        print(f"Raw result from DB: {result}", flush=True)
        
        if result and result[0] is not None:
            value = int(result[0])
            print(f"Returning: {value}", flush=True)
            return value
        else:
            print("No value found, returning 10", flush=True)
            return 10
            
    except Exception as e:
        print(f"Error: {e}", flush=True)
        return 10
    finally:
        conn.close()

#--------------------------
#    🔹 دوال مساعدة اعدادات config المستخدمين
#--------------------------
def set_user_has_quizzes(user_id):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        UPDATE users 
        SET has_quizzes = 1 
        WHERE user_id = ?
    """, (user_id,))
    
    conn.commit()
    conn.close()

def user_has_quizzes(user_id):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT has_quizzes FROM users 
        WHERE user_id = ?
    """, (user_id,))
    
    result = c.fetchone()
    conn.close()
    
    # ترجع True إذا كانت القيمة 1، وإلا False
    return result is not None and result[0] == 1
    
#--------------------------
#    🔹 دوال مساعدة user_major
#--------------------------
def get_user_major(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT major FROM users WHERE user_id = ?
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None


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
    


#--------------------------
#    🔹 users management 
#--------------------------
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


#--------------------------
#    🔹 دوال الأخطاء للمستخدم
#--------------------------
def calculate_daily_review_limit(user_id):
    stats = get_user_mistakes_stats(user_id)
    total_mistakes = stats["total_mistakes"]
    
    # القاعدة: 10 أسئلة أساسية + (عدد الأخطاء الكلية ÷ 5)
    # مثال: 50 خطأ → 10 + (50÷5) = 20 سؤال يومياً
    # بحد أقصى 30 سؤال يومياً لتجنب الإرهاق
    
    base_limit = 10
    dynamic_bonus = total_mistakes // 5
    daily_limit = min(base_limit + dynamic_bonus, 30)
    
    return daily_limit
    
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
    
    # الأخطاء في آخر 7 أيام (عدد الأسئلة الفريدة)
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    c.execute("""
        SELECT COUNT(*) FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0 AND last_failed > ?
    """, (user_id, week_ago))
    
    week_mistakes = c.fetchone()[0]
    
    # الأخطاء في آخر 24 ساعة (للنشاط الحديث)
    day_ago = (datetime.now() - timedelta(days=1)).isoformat()
    c.execute("""
        SELECT COUNT(*) FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0 AND last_failed > ?
    """, (user_id, day_ago))
    
    recent_mistakes = c.fetchone()[0]
    
    # الأخطاء الفعلية في آخر 7 أيام (ككائنات للمراجعة)
    c.execute("""
        SELECT id, question_text, options, correct_index, explanation, 
               fail_count, last_failed
        FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0 AND last_failed > ?
        ORDER BY last_failed DESC
    """, (user_id, week_ago))
    
    week_mistakes_list = []
    for row in c.fetchall():
        week_mistakes_list.append({
            "id": row[0],
            "question_text": row[1],
            "options": json.loads(row[2]),
            "correct_index": row[3],
            "explanation": row[4],
            "fail_count": row[5],
            "last_failed": row[6]
        })
    
    # الأخطاء الفعلية في آخر 24 ساعة
    c.execute("""
        SELECT id, question_text, options, correct_index, explanation, 
               fail_count, last_failed
        FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0 AND last_failed > ?
        ORDER BY last_failed DESC
    """, (user_id, day_ago))
    
    recent_mistakes_list = []
    for row in c.fetchall():
        recent_mistakes_list.append({
            "id": row[0],
            "question_text": row[1],
            "options": json.loads(row[2]),
            "correct_index": row[3],
            "explanation": row[4],
            "fail_count": row[5],
            "last_failed": row[6]
        })
    
    # متوسط تكرار الخطأ لكل سؤال
    c.execute("""
        SELECT AVG(fail_count) FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0
    """, (user_id,))
    
    avg_fail = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_mistakes": total_mistakes,
        "week_mistakes_count": week_mistakes,           # عدد الأخطاء في آخر 7 أيام
        "week_mistakes_list": week_mistakes_list,       # قائمة الأخطاء في آخر 7 أيام
        "recent_mistakes_count": recent_mistakes,       # عدد الأخطاء في آخر 24 ساعة
        "recent_mistakes_list": recent_mistakes_list,   # قائمة الأخطاء في آخر 24 ساعة
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

def get_smart_review_batch(user_id, limit):
    """ترجع مجموعة ذكية من الأسئلة للمراجعة"""
    conn = get_connection()
    c = conn.cursor()
    
    # 60% من الأخطاء الأكثر تكراراً (نقاط الضعف القوية)
    high_priority_limit = int(limit * 0.6)
    c.execute("""
        SELECT id, question_text, options, correct_index, 
               explanation, fail_count, last_failed, created_at
        FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0
        ORDER BY fail_count DESC, last_failed DESC
        LIMIT ?
    """, (user_id, high_priority_limit))
    
    high_priority = c.fetchall()
    
    # 40% من الأخطاء الأقدم (لمنع النسيان)
    old_limit = limit - len(high_priority)
    c.execute("""
        SELECT id, question_text, options, correct_index, 
               explanation, fail_count, last_failed, created_at
        FROM user_mistakes 
        WHERE user_id = ? AND fail_count > 0
        AND id NOT IN ({})
        ORDER BY created_at ASC, last_failed ASC
        LIMIT ?
    """.format(','.join(['?']*len(high_priority)) if high_priority else '0'), 
       (user_id, *[m[0] for m in high_priority], old_limit))
    
    old_mistakes = c.fetchall()
    
    conn.close()
    
    # دمج النتائج وتحويلها للصيغة المطلوبة
    all_mistakes = list(high_priority) + list(old_mistakes)
    
    return [{
        "id": m[0],
        "questions": {
            "question": m[1],
            "options": json.loads(m[2]),
            "correct_index": m[3],
            "explanation": m[4]
        },
        "fail_count": m[5],
        "priority": "high" if m in high_priority else "old"
    } for m in all_mistakes]


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

    if not column_exists("users", "pro_quota"):
        c.execute("""
        ALTER TABLE users ADD COLUMN pro_quota INTEGER DEFAULT 5
        """)
        

    if not column_exists("user_mistakes", "created_at"):
        c.execute("""
        ALTER TABLE user_mistakes ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP 
        """)
    if not column_exists("users_trap", "last_quiz_time"):
        c.execute("""
        ALTER TABLE users_trap ADD COLUMN last_quiz_time TEXT 
        """)

    if not column_exists("user_mistakes", "branch"):
        c.execute("""
        ALTER TABLE user_mistakes ADD COLUMN branch TEXT 
        """)
    if not column_exists("users", "has_quizzes"):
        c.execute("""
        ALTER TABLE users ADD COLUMN has_quizzes BOOLEAN DEFAULT 0 
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

    



