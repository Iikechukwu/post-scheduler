import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect("scheduler.db")
    c = conn.cursor()
    # Updated table with 'status' and 'category'
    c.execute('''CREATE TABLE IF NOT EXISTS posts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, time TEXT, caption TEXT, image TEXT, 
                  status TEXT DEFAULT 'Scheduled',
                  category TEXT DEFAULT 'General')''')
    conn.commit()
    conn.close()

def add_post(date, time, caption, image, category="General"):
    conn = sqlite3.connect("scheduler.db")
    c = conn.cursor()
    c.execute("INSERT INTO posts (date, time, caption, image, status, category) VALUES (?, ?, ?, ?, 'Scheduled', ?)", 
              (date, time, caption, image, category))
    conn.commit()
    conn.close()

def get_all_posts():
    conn = sqlite3.connect("scheduler.db")
    c = conn.cursor()
    c.execute("SELECT * FROM posts ORDER BY date DESC, time DESC")
    posts = c.fetchall()
    conn.close()
    return posts
