# storage/sqlite_db.py

import sqlite3

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
#    🔹 دوال مساعدة
#--------------------------
def save_user_knowledge(user_id, last_text, specialty):
    conn = get_connection()
    c = conn.cursor()
    
    # التحقق من حالة المستخدم
    if is_paid_user_active(user_id):
        # المستخدم المدفوع: يخزن 10 نصوص
        
        # إدراج النص الجديد
        c.execute("""
            INSERT INTO user_knowledge (user_id, last_text, specialty, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, last_text, specialty))
        
        # التحقق من العدد الإجمالي
        c.execute("""
            SELECT COUNT(*) FROM user_knowledge WHERE user_id = ?
        """, (user_id,))
        
        count = c.fetchone()[0]
        
        # إذا تجاوز 10، احذف الأقدم
        if count > 10:
            c.execute("""
                DELETE FROM user_knowledge 
                WHERE id IN (
                    SELECT id FROM user_knowledge 
                    WHERE user_id = ? 
                    ORDER BY updated_at ASC 
                    LIMIT ?
                )
            """, (user_id, count - 10))
    
    else:
        # المستخدم العادي: يخزن آخر نص فقط (يستبدل كل مرة)
        c.execute("""
            INSERT OR REPLACE INTO user_knowledge (id, user_id, last_text, specialty, updated_at)
            VALUES (
                COALESCE((SELECT id FROM user_knowledge WHERE user_id = ?), NULL),
                ?, ?, ?, CURRENT_TIMESTAMP
            )
        """, (user_id, user_id, last_text, specialty))
    
    conn.commit()
    conn.close()
    
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

    



