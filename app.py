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

    def safe_load_image(self, image_path):
        """Load image safely, handling both URLs and local file paths."""
        if not image_path:
            return None
        
        # If it's a URL (starts with http)
        if isinstance(image_path, str) and image_path.startswith("http"):
            return image_path
        
        # If it's a local file path
        if isinstance(image_path, str):
            full_path = os.path.join(os.getcwd(), image_path)
            if os.path.exists(full_path):
                return full_path
            elif os.path.exists(image_path):
                return image_path
        
        # Return placeholder if file not found
        return "https://via.placeholder.com/400x300?text=Image+Not+Found"

    @st.dialog("Edit Post")
    def edit_modal(self, post_id, old_cap, old_date, old_time):
        new_cap = st.text_area("Update Caption", value=old_cap)
        new_d = st.date_input("Update Date", value=datetime.strptime(old_date, "%Y-%m-%d"))
        new_t = st.time_input("Update Time", value=datetime.strptime(old_time, "%H:%M"))
        if st.button("Save Changes"):
            self.db.update_post(post_id, new_d.strftime("%Y-%m-%d"), new_t.strftime("%H:%M"), new_cap)
            st.rerun()

    def run(self):
        st.title("📱 Social Media Post Scheduler")

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
            
            if st.button("🚀Post"):
                final_img = selected_img
                if source == "Upload from PC" and local_file:
                    final_img = os.path.join("uploads", local_file.name)
                    with open(final_img, "wb") as f:
                        f.write(local_file.getbuffer())
                self.db.add_post(d.strftime("%Y-%m-%d"), t.strftime("%H:%M"), cap, final_img, cat)
                st.success("Saved!")
                st.rerun()

        with col_pre:
            st.subheader("Preview")
            if source == "Upload from PC" and local_file:
                st.image(local_file, use_column_width=True)
            else:
                st.image(selected_img, use_column_width=True)

        # Feed Section
        st.divider()
        st.subheader("🗓️ Content Calendar")
        search_term = st.text_input("🔍 Search your posts...", placeholder="Keyword or category...")
        
        posts = self.db.search_posts(search_term) if search_term else self.db.get_all_posts()

        if not posts:
            st.write("No matching posts found.")
        else:
            for post in posts:
                # Handle both old (7-col) and new (9-col) schema
                if len(post) >= 9:
                    p_id, p_date, p_time, p_cap, p_img, p_status, p_cat, p_fb_id, p_error = post[:9]
                else:
                    p_id, p_date, p_time, p_cap, p_img, p_status, p_cat = post
                    p_fb_id, p_error = None, None
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c1:
                        img_path = self.safe_load_image(p_img)
                        st.image(img_path, use_column_width=True)
                    with c2:
                        if p_status == "Published":
                            badge_color = "green"
                            status_text = "✅ Published"
                        elif p_status == "Failed":
                            badge_color = "red"
                            status_text = "❌ Failed"
                        else:
                            badge_color = "orange"
                            status_text = "⏳ Scheduled"
                        
                        st.markdown(f":{badge_color}[**{status_text}**] | `{p_cat}`")
                        st.write(f"📅 **{p_date}** at **{p_time}**")
                        st.write(p_cap)
                        
                        if p_status == "Published" and p_fb_id:
                            st.caption(f"📱 Facebook ID: {p_fb_id}")
                        elif p_status == "Failed" and p_error:
                            st.error(f"Post failed: {p_error}")
                    
                    with c3:
                        if st.button("✏️ Edit", key=f"ed_{p_id}"):
                            self.edit_modal(p_id, p_cap, p_date, p_time)
                        if st.button("🗑️ Delete", key=f"del_{p_id}"):
                            self.db.delete_post(p_id)
                            st.rerun()

# Execute the application
if __name__ == "__main__":
    app = SocialMediaApp()
    app.run()