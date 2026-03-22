# storage/sqlite_db.py

import sqlite3

DB_PATH = "quiz_users.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

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
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_code TEXT,
        user_id INTEGER,
        score INTEGER,
        total INTEGER,
        timestamp TEXT
        UNIQUE(user_id, quiz_code)
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

    if not column_exists("users", "current_quiz_selection"):
        c.execute("""
        ALTER TABLE users ADD COLUMN current_quiz_selection TEXT DEFAULT 'sample_quiz'
        """)

    if not column_exists("user_quizzes", "is_paid"):
        c.execute("""
        ALTER TABLE user_quizzes ADD COLUMN is_paid BOOLEAN DEFAULT 0
        """)

    conn.commit()
    conn.close()

    print("✅ Schema updated safely")





    



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
#      تحليل الاداء للسمتخدمين    
#-----------------------------
def get_quiz_stats(quiz_code):
    conn = get_connection()
    c = conn.cursor()

    # عدد المحاولات
    c.execute("""
        SELECT COUNT(*) FROM quiz_attempts WHERE quiz_code=?
    """, (quiz_code,))
    attempts = c.fetchone()[0]

    # عدد المستخدمين الفريدين
    c.execute("""
        SELECT COUNT(DISTINCT user_id) FROM quiz_attempts WHERE quiz_code=?
    """, (quiz_code,))
    users = c.fetchone()[0]

    # عدد المكتملين (score != NULL)
    c.execute("""
        SELECT COUNT(*) FROM quiz_attempts 
        WHERE quiz_code=? AND score IS NOT NULL
    """, (quiz_code,))
    completed = c.fetchone()[0]

    conn.close()

    return {
        "attempts": attempts,
        "users": users,
        "completed": completed
    }


#--------------------------
#    تسجيل كل محاولة 
#-----------------------------
from datetime import datetime
from storage.sqlite_db import get_connection

def log_quiz_attempt(user_id, quiz_code, score, total):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO quiz_attempts (quiz_code, user_id, score, total, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        quiz_code,
        user_id,
        score,
        total,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


#--------------------------
#      أفضل المستخدمين (Leaderboard)    
#-----------------------------
def get_top_users(quiz_code, limit=5):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT user_id, score 
        FROM quiz_attempts
        WHERE quiz_code=?
        ORDER BY score DESC
        LIMIT ?
    """, (quiz_code, limit))

    rows = c.fetchall()
    conn.close()

    return rows


#--------------------------
#      . أسماء المستخدمين (اختياري)    
#---------------------------
def format_usernames(bot, user_ids):
    names = []
    for uid in user_ids:
        try:
            user = bot.get_chat(uid)
            names.append(user.first_name)
        except:
            continue
    return names


#--------------------------
#      رسالة Upsell الذكية
#--------------------------
def build_quiz_viral_message(stats, names):
    sample_names = "\n".join([f"- {n}" for n in names[:3]])

    return f"""
🔥 اختبارك بدأ ينتشر!

👥 {stats['users']} شخصاً جربوه  
📊 {stats['completed']} أكملوه

👀 بعض الأسماء:
{sample_names}

━━━━━━━━━━━━━━━
🔓 افتح الإحصائيات الكاملة وتحليل الأداء مع TestGenie Pro
"""


