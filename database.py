import sqlite3
import datetime

class DatabaseManager:
    def __init__(self, db_name="scheduler.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS posts 
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          date TEXT, time TEXT, caption TEXT, image TEXT, 
                          status TEXT DEFAULT 'Scheduled',
                          category TEXT DEFAULT 'General')''')
            conn.commit()

    def add_post(self, date, time, caption, image, category="General"):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO posts (date, time, caption, image, status, category) VALUES (?, ?, ?, ?, 'Scheduled', ?)", 
                      (date, time, caption, image, category))
            conn.commit()

    def get_all_posts(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM posts ORDER BY date DESC, time DESC")
            return c.fetchall()

    def delete_post(self, post_id):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM posts WHERE id=?", (post_id,))
            conn.commit()

    def update_post(self, post_id, date, time, caption):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("UPDATE posts SET date=?, time=?, caption=? WHERE id=?", 
                      (date, time, caption, post_id))
            conn.commit()

    def get_stats(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT status, COUNT(*) FROM posts GROUP BY status")
            return dict(c.fetchall())

    def check_and_publish(self):
        now = datetime.datetime.now()
        curr_date = now.strftime("%Y-%m-%d")
        curr_time = now.strftime("%H:%M")
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("UPDATE posts SET status='Published' WHERE status='Scheduled' AND (date < ? OR (date = ? AND time <= ?))", 
                      (curr_date, curr_date, curr_time))
            conn.commit()

    def search_posts(self, query):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM posts WHERE caption LIKE ? OR category LIKE ? ORDER BY date DESC", 
                      (f'%{query}%', f'%{query}%'))
            return c.fetchall()
