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