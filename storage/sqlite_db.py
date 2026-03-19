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
    CREATE TABLE referrals (
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
    CREATE TABLE IF NOT EXISTS sample_quizzes (
        quiz_code TEXT PRIMARY KEY,
        quiz_data TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # أضف العمود الجديد في أمر منفصل
    cursor.execute("ALTER TABLE users ADD COLUMN free_quizzes INTEGER DEFAULT 3;")
    cursor.execute("ALTER TABLE users ADD COLUMN invited_by INTEGER;")
    cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

    
    
    conn.commit()
    conn.close()



"""
    cursor.execute(
    CREATE TABLE IF NOT EXISTS quiz_attempts (
id INTEGER PRIMARY KEY AUTOINCREMENT,
quiz_code TEXT,
user_id INTEGER,
score INTEGER,
total INTEGER,
timestamp TEXT
)
)
"""
