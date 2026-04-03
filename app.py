import streamlit as st
import json
from datetime import datetime
from scheduler import PostScheduler
from models import Post, Platform
from history import PostHistory

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PostFlow · Social Scheduler",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* Reset & base */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

/* App background */
.stApp {
    background: #0a0a0f;
    color: #e8e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111118 !important;
    border-right: 1px solid #1e1e2e;
}
[data-testid="stSidebar"] * { color: #c8c8d8 !important; }

/* Cards */
.card {
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: #3d3d5c; }

/* Platform badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-twitter  { background: #1a1f2e; color: #1d9bf0; border: 1px solid #1d9bf0; }

/* Status badges */
.status-scheduled  { background: #1a2e1a; color: #4ade80; border: 1px solid #4ade80; }
.status-published  { background: #1a1f2e; color: #60a5fa; border: 1px solid #60a5fa; }
.status-failed     { background: #2e1a1a; color: #f87171; border: 1px solid #f87171; }
.status-draft      { background: #2e2a1a; color: #fbbf24; border: 1px solid #fbbf24; }

/* Heading accent */
.accent { color: #a78bfa; }
.mono { font-family: 'DM Mono', monospace; font-size: 0.85rem; }

/* Metric cards */
.metric-box {
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.metric-number {
    font-size: 2.2rem;
    font-weight: 700;
    color: #a78bfa;
    font-family: 'DM Mono', monospace;
}
.metric-label {
    font-size: 0.78rem;
    color: #666680;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.2rem;
}

/* Divider */
hr { border-color: #1e1e2e !important; }

/* Input overrides */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #0d0d15 !important;
    border-color: #1e1e2e !important;
    color: #e8e8f0 !important;
    border-radius: 8px !important;
}
.stDateInput input, .stTimeInput input {
    background: #0d0d15 !important;
    color: #e8e8f0 !important;
}

/* Button */
.stButton > button {
    background: #a78bfa !important;
    color: #0a0a0f !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: #1e1e2e !important;
    color: #c8c8d8 !important;
}

/* Success / error / info boxes */
.stSuccess { background: #0f1f0f !important; border-color: #4ade80 !important; }
.stError   { background: #1f0f0f !important; border-color: #f87171 !important; }
.stInfo    { background: #0f0f1f !important; border-color: #a78bfa !important; }
.stWarning { background: #1f1a0f !important; border-color: #fbbf24 !important; }

/* Post card list */
.post-card {
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
}
.post-content {
    color: #c8c8d8;
    font-size: 0.92rem;
    line-height: 1.6;
    margin: 0.5rem 0;
    white-space: pre-wrap;
}
.post-meta {
    color: #555570;
    font-size: 0.78rem;
    font-family: 'DM Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "scheduler" not in st.session_state:
    st.session_state.scheduler = PostScheduler()
if "history" not in st.session_state:
    st.session_state.history = PostHistory()
if "active_page" not in st.session_state:
    st.session_state.active_page = "Schedule"

scheduler: PostScheduler = st.session_state.scheduler
history: PostHistory = st.session_state.history

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 PostFlow")
    st.markdown('<p class="mono" style="color:#555570;">Social Media Scheduler</p>', unsafe_allow_html=True)
    st.markdown("---")

    pages = ["📅 Schedule", "📋 Queue", "📊 History", "⚙️ Settings"]
    page_labels = {p.split(" ", 1)[1]: p for p in pages}

    for page in pages:
        label = page.split(" ", 1)[1]
        if st.button(page, use_container_width=True,
                     type="primary" if st.session_state.active_page == label else "secondary"):
            st.session_state.active_page = label
            st.rerun()

    st.markdown("---")
    # Quick stats
    all_posts = history.get_all_posts()
    scheduled = scheduler.get_scheduled_posts()
    st.markdown(f"""
    <div class="metric-box" style="margin-bottom:0.5rem">
        <div class="metric-number">{len(scheduled)}</div>
        <div class="metric-label">Queued</div>
    </div>
    <div class="metric-box">
        <div class="metric-number">{len(all_posts)}</div>
        <div class="metric-label">Total Posts</div>
    </div>
    """, unsafe_allow_html=True)

active = st.session_state.active_page

# ── Page: Schedule ────────────────────────────────────────────────────────────
if active == "Schedule":
    st.markdown("# <span class='accent'>Schedule</span> a Post", unsafe_allow_html=True)
    st.markdown("Compose your message and choose when & where to publish it.")
    st.markdown("---")

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.markdown("#### ✍️ Compose")
        content = st.text_area(
            "Post content",
            height=160,
            placeholder="What do you want to share?",
            max_chars=2200,
            label_visibility="collapsed"
        )

        char_count = len(content)
        TWITTER_LIMIT = 280

        st.markdown("**Platform: 🐦 Twitter / X**")

        # Character count indicator
        if content:
            pct   = char_count / TWITTER_LIMIT
            color = "#4ade80" if pct < 0.8 else "#fbbf24" if pct < 1 else "#f87171"
            st.markdown(
                f'<p class="mono" style="color:{color};">Characters: {char_count}/{TWITTER_LIMIT}</p>',
                unsafe_allow_html=True
            )

    with col2:
        st.markdown("#### 🕐 Schedule")
        post_date = st.date_input("Date", min_value=datetime.today().date())
        post_time = st.time_input("Time", value=datetime.now().time().replace(second=0, microsecond=0))
        post_mode = st.radio("Mode", ["Scheduled", "Draft", "Publish Now"])

        st.markdown("#### 🔗 API Keys")
        with st.expander("Configure Twitter credentials", expanded=False):
            st.caption("All four values are required. Find them in your Twitter Developer App → Keys and Tokens.")
            tw_api_key    = st.text_input("API Key (Consumer Key)",    type="password", value=st.session_state.get("tw_api_key", ""))
            tw_api_secret = st.text_input("API Key Secret",            type="password", value=st.session_state.get("tw_api_secret", ""))
            tw_acc_token  = st.text_input("Access Token",              type="password", value=st.session_state.get("tw_acc_token", ""))
            tw_acc_secret = st.text_input("Access Token Secret",       type="password", value=st.session_state.get("tw_acc_secret", ""))
            if st.button("Save Keys"):
                st.session_state.tw_api_key   = tw_api_key
                st.session_state.tw_api_secret = tw_api_secret
                st.session_state.tw_acc_token  = tw_acc_token
                st.session_state.tw_acc_secret = tw_acc_secret
                st.success("Twitter credentials saved for this session.")

    st.markdown("---")
    btn_col1, btn_col2 = st.columns([1, 5])
    with btn_col1:
        submit = st.button("✅ Schedule Post", use_container_width=True)

    if submit:
        try:
            if not content.strip():
                raise ValueError("Post content cannot be empty.")

            scheduled_dt = datetime.combine(post_date, post_time)
            if post_mode == "Scheduled" and scheduled_dt < datetime.now():
                raise ValueError("Scheduled time must be in the future.")

            credentials = {
                "api_key":             st.session_state.get("tw_api_key", ""),
                "api_key_secret":      st.session_state.get("tw_api_secret", ""),
                "access_token":        st.session_state.get("tw_acc_token", ""),
                "access_token_secret": st.session_state.get("tw_acc_secret", ""),
            }

            post = Post(
                content=content,
                platform=Platform.TWITTER,
                scheduled_time=scheduled_dt,
                status=post_mode.upper().replace(" ", "_"),
            )

            if post_mode == "Publish Now":
                result = scheduler.publish_now(post, credentials)
                history.add_post(post)
                st.success(f"✅ Published to Twitter / X: {result}")
            else:
                scheduler.schedule_post(post)
                history.add_post(post)
                st.success(f"📅 Post queued for {scheduled_dt.strftime('%b %d, %Y %H:%M')}")

        except ValueError as ve:
            st.error(f"⚠️ Validation error: {ve}")
        except ConnectionError as ce:
            st.error(f"🔌 Connection error: {ce}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

# ── Page: Queue ───────────────────────────────────────────────────────────────
elif active == "Queue":
    st.markdown("# Scheduled <span class='accent'>Queue</span>", unsafe_allow_html=True)
    st.markdown("Posts waiting to be published.")
    st.markdown("---")

    queued = scheduler.get_scheduled_posts()

    if not queued:
        st.info("📭 No posts in the queue. Head to **Schedule** to add one!")
    else:
        # Check if any posts are due
        due_posts = scheduler.check_due_posts()
        if due_posts:
            st.warning(f"⏰ {len(due_posts)} post(s) are due for publishing!")
            if st.button("🚀 Publish Due Posts"):
                published, failed = scheduler.publish_due_posts(
                    credentials={
                        "api_key":             st.session_state.get("tw_api_key", ""),
                        "api_key_secret":      st.session_state.get("tw_api_secret", ""),
                        "access_token":        st.session_state.get("tw_acc_token", ""),
                        "access_token_secret": st.session_state.get("tw_acc_secret", ""),
                    }
                )
                for p in published:
                    history.update_post_status(p.id, "PUBLISHED")
                    st.success(f"Published: {p.content[:60]}...")
                for p, err in failed:
                    history.update_post_status(p.id, "FAILED")
                    st.error(f"Failed ({p.platform.value}): {err}")
                st.rerun()

        for i, post in enumerate(sorted(queued, key=lambda p: p.scheduled_time)):
            icon, badge_cls, label = "🐦", "badge-twitter", "Twitter / X"
            st.markdown(f"""
            <div class="post-card">
                <span class="badge {badge_cls}">{icon} {label}</span>&nbsp;
                <span class="badge status-{post.status.lower()}">{post.status}</span>
                <p class="post-content">{post.content}</p>
                <span class="post-meta">🕐 {post.scheduled_time.strftime('%A, %b %d %Y at %H:%M')} &nbsp;·&nbsp; ID: {post.id[:8]}</span>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b, _ = st.columns([1, 1, 6])
            with col_a:
                if st.button("🗑 Remove", key=f"del_{post.id}"):
                    try:
                        scheduler.remove_post(post.id)
                        history.update_post_status(post.id, "CANCELLED")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not remove: {e}")
            with col_b:
                if st.button("✏️ Edit", key=f"edit_{post.id}"):
                    st.session_state["editing_post"] = post
                    st.session_state.active_page = "Schedule"
                    st.rerun()

# ── Page: History ─────────────────────────────────────────────────────────────
elif active == "History":
    st.markdown("# Post <span class='accent'>History</span>", unsafe_allow_html=True)
    st.markdown("A log of every post you've created.")
    st.markdown("---")

    all_posts = history.get_all_posts()

    # Metrics row
    published = [p for p in all_posts if p.get("status") == "PUBLISHED"]
    failed    = [p for p in all_posts if p.get("status") == "FAILED"]
    drafts    = [p for p in all_posts if p.get("status") == "DRAFT"]

    m1, m2, m3, m4 = st.columns(4)
    for col, val, label in [
        (m1, len(all_posts),  "Total"),
        (m2, len(published),  "Published"),
        (m3, len(failed),     "Failed"),
        (m4, len(drafts),     "Drafts"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-number">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Filters
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        filter_status = st.selectbox("Filter by status", ["All", "PUBLISHED", "SCHEDULED", "FAILED", "DRAFT", "CANCELLED"])
    with fcol2:
        filtered = all_posts
    if filter_status != "All":
        filtered = [p for p in filtered if p.get("status") == filter_status]

    if not filtered:
        st.info("No posts match the selected filters.")
    else:
        status_cls = {"PUBLISHED": "status-published", "FAILED": "status-failed",
                      "DRAFT": "status-draft", "SCHEDULED": "status-scheduled"}
        plat_cls   = {"twitter": "badge-twitter"}

        for post in reversed(filtered):
            sc  = status_cls.get(post.get("status", ""), "badge")
            pc  = plat_cls.get(post.get("platform", ""), "badge")
            ts  = post.get("scheduled_time", "—")
            pid = post.get("id", "")[:8]
            st.markdown(f"""
            <div class="post-card">
                <span class="badge {pc}">{post.get('platform','').capitalize()}</span>&nbsp;
                <span class="badge {sc}">{post.get('status','')}</span>
                <p class="post-content">{post.get('content','')}</p>
                <span class="post-meta">🕐 {ts} &nbsp;·&nbsp; ID: {pid}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🗑️ Clear All History"):
            history.clear_history()
            st.rerun()

        # Export
        if st.download_button(
            "⬇️ Export History (JSON)",
            data=json.dumps(filtered, indent=2, default=str),
            file_name=f"postflow_history_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        ):
            st.success("History exported!")

# ── Page: Settings ────────────────────────────────────────────────────────────
elif active == "Settings":
    st.markdown("# ⚙️ <span class='accent'>Settings</span>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 🔑 Twitter API Configuration")
    st.info(
        "PostFlow uses **OAuth 1.0a User Context** — the method required to post tweets. "
        "You need all **four credentials** from your Twitter Developer App."
    )
    st.warning(
        "⚠️ Important: After setting your app permissions to **Read and Write**, "
        "you must **Regenerate** your Access Token and Access Token Secret. "
        "Old tokens won't inherit the new permission level."
    )

    with st.form("api_form"):
        st.markdown("Find all four values in your **Twitter Developer Portal → App → Keys and Tokens**.")
        tw_api_key    = st.text_input("API Key (Consumer Key)",    type="password", value=st.session_state.get("tw_api_key", ""))
        tw_api_secret = st.text_input("API Key Secret",            type="password", value=st.session_state.get("tw_api_secret", ""))
        tw_acc_token  = st.text_input("Access Token",              type="password", value=st.session_state.get("tw_acc_token", ""))
        tw_acc_secret = st.text_input("Access Token Secret",       type="password", value=st.session_state.get("tw_acc_secret", ""))
        if st.form_submit_button("💾 Save Settings"):
            st.session_state.tw_api_key    = tw_api_key
            st.session_state.tw_api_secret = tw_api_secret
            st.session_state.tw_acc_token  = tw_acc_token
            st.session_state.tw_acc_secret = tw_acc_secret
            st.success("✅ Twitter credentials saved for this session.")

    st.markdown("---")
    st.markdown("### ℹ️ About PostFlow")
    st.markdown("""
<div class="card">
<b>PostFlow</b> is a social media scheduling tool built for a Python OOP class project.<br><br>
<b>Tech stack:</b> Python · Streamlit · Twitter API v2<br>
<b>Key concepts:</b> Object-Oriented Programming · Exception Handling · REST APIs · JSON persistence<br><br>
<span class="mono" style="color:#555570;">PostFlow v1.0.0</span>
</div>
""", unsafe_allow_html=True)
