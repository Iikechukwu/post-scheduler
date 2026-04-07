import streamlit as st
from datetime import datetime
import os
from database import DatabaseManager
from unsplash_service import UnsplashService
from apscheduler.schedulers.background import BackgroundScheduler

class SocialMediaApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.api = UnsplashService()
        self.setup_environment()
        self.start_scheduler()

    def setup_environment(self):
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        st.set_page_config(page_title="Social Media Pro (OOP)", layout="wide")

    def start_scheduler(self):
        if "scheduler_started" not in st.session_state:
            scheduler = BackgroundScheduler()
            # Pass the class method to the scheduler
            scheduler.add_job(self.db.check_and_publish, 'interval', minutes=1)
            scheduler.start()
            st.session_state.scheduler_started = True

    @st.dialog("Edit Post")
    def edit_modal(self, post_id, old_cap, old_date, old_time):
        new_cap = st.text_area("Update Caption", value=old_cap)
        new_d = st.date_input("Update Date", value=datetime.strptime(old_date, "%Y-%m-%d"))
        new_t = st.time_input("Update Time", value=datetime.strptime(old_time, "%H:%M"))
        if st.button("Save Changes"):
            self.db.update_post(post_id, new_d.strftime("%Y-%m-%d"), new_t.strftime("%H:%M"), new_cap)
            st.rerun()

    def run(self):
        st.title("📱 Content Strategy Dashboard")

        # Metrics Section
        stats = self.db.get_stats()
        s1, s2, s3 = st.columns(3)
        s1.metric("Total Content", sum(stats.values()))
        s2.metric("Scheduled", stats.get('Scheduled', 0))
        s3.metric("Live Posts", stats.get('Published', 0))

        st.divider()

        # Input Section
        st.sidebar.header("🔍 Unsplash Search")
        query = st.sidebar.text_input("Find inspiration", "Minimalism")
        selected_img = self.api.fetch_image(query)

        col_in, col_pre = st.columns(2)
        with col_in:
            st.subheader("New Post")
            cap = st.text_area("What's on your mind?")
            cat = st.selectbox("Category", ["Marketing", "Personal", "Educational", "Meme"])
            source = st.radio("Image Source", ["Unsplash Search", "Upload from PC"])
            
            local_file = None
            if source == "Upload from PC":
                local_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
            
            d = st.date_input("Schedule Date", datetime.now())
            t = st.time_input("Schedule Time", datetime.now())
            
            if st.button("🚀 Save Post"):
                final_img = selected_img
                if source == "Upload from PC" and local_file:
                    final_img = os.path.join("uploads", local_file.name)
                    with open(final_img, "wb") as f:
                        f.write(local_file.getbuffer())
                self.db.add_post(d.strftime("%Y-%m-%d"), t.strftime("%H:%M"), cap, final_img, cat)
                st.success("Saved!")
                st.rerun()