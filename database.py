import sqlite3
import datetime
from facebook_service import FacebookService

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
                          category TEXT DEFAULT 'General',
                          facebook_post_id TEXT,
                          error_message TEXT)''')
            conn.commit()
            # Add columns if they don't exist (for existing databases)
            try:
                c.execute("ALTER TABLE posts ADD COLUMN facebook_post_id TEXT")
                c.execute("ALTER TABLE posts ADD COLUMN error_message TEXT")
                conn.commit()
            except:
                pass

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
        fb_service = FacebookService()
        
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            # Find posts that are due
            c.execute("SELECT id, caption, image FROM posts WHERE status='Scheduled' AND (date < ? OR (date = ? AND time <= ?))", 
                      (curr_date, curr_date, curr_time))
            due_posts = c.fetchall()
            
            for post_id, caption, image_url in due_posts:
                # Attempt to post to Facebook
                success, fb_post_id, error = fb_service.post_to_feed(caption, image_url)
                
                if success:
                    c.execute("UPDATE posts SET status='Published', facebook_post_id=? WHERE id=?", 
                              (fb_post_id, post_id))
                else:
                    c.execute("UPDATE posts SET status='Failed', error_message=? WHERE id=?", 
                              (error, post_id))
            
            conn.commit()

    def search_posts(self, query):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM posts WHERE caption LIKE ? OR category LIKE ? ORDER BY date DESC", 
                      (f'%{query}%', f'%{query}%'))
            return c.fetchall()
