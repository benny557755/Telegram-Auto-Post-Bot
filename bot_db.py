import sqlite3

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Posts သိမ်းဆည်းရန် Table (file_id ကို TEXT အဖြစ်ထားခြင်းက Poll JSON သိမ်းဖို့ အဆင်ပြေစေပါတယ်)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            caption TEXT,
            file_type TEXT,
            is_posted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Settings သိမ်းဆည်းရန် Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Default settings သတ်မှတ်ခြင်း
    defaults = [
        ('daily_limit', '5'),
        ('delete_after_post', '0'),
        ('watermark_text', '@Benny875'),
        ('post_schedule', '') 
    ]
    cursor.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", defaults)
    
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def set_setting(key, value):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def add_post(file_id, caption, file_type):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO posts (file_id, caption, file_type) VALUES (?, ?, ?)", 
                   (file_id, caption, file_type))
    conn.commit()
    conn.close()

def get_random_post():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_id, caption, file_type FROM posts WHERE is_posted=0 ORDER BY RANDOM() LIMIT 1")
    res = cursor.fetchone()
    conn.close()
    return res

def mark_as_posted(post_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    delete_after = get_setting('delete_after_post')
    if delete_after == '1':
        cursor.execute("DELETE FROM posts WHERE id=?", (post_id,))
    else:
        cursor.execute("UPDATE posts SET is_posted=1 WHERE id=?", (post_id,))
    conn.commit()
    conn.close()

def delete_single_post_db(post_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()