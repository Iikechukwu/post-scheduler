# 📡 PostFlow — Twitter Post Scheduler

A Python + Streamlit social media scheduler built for an OOP class project.
Supports **Twitter / X** via the Twitter API v2.

---

## Project Structure

```
social_scheduler/
├── app.py           # Streamlit UI (entry point)
├── models.py        # Post & Platform classes (data layer)
├── scheduler.py     # PostScheduler class (business logic)
├── api_clients.py   # SocialMediaClient ABC + TwitterClient (API layer)
├── history.py       # PostHistory class (JSON persistence)
├── secrets.toml     # ← YOUR API KEY GOES HERE (see guide below)
├── requirements.txt
└── README.md
```

---

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## OOP Concepts Demonstrated

| Concept | Where |
|---|---|
| Classes & instances | `Post`, `PostScheduler`, `PostHistory`, `TwitterClient` |
| Dataclass | `Post` (using `@dataclass`) |
| Inheritance | `TwitterClient` → `SocialMediaClient` |
| Abstract Base Class | `SocialMediaClient` (ABC with `@abstractmethod`) |
| Encapsulation | Private `_queue` in `PostScheduler`, `_records` in `PostHistory` |
| Polymorphism | `client.publish(post)` interface defined in base class |
| Enums | `Platform` enum |
| Factory pattern | `ClientFactory.create(platform, token)` |
| Custom exceptions | `APIError`, `AuthenticationError`, `RateLimitError`, `NetworkError`, `SchedulerError`, `HistoryError` |
| Exception hierarchy | `AuthenticationError` and `RateLimitError` both inherit from `APIError` |

---

## 🔑 How to Get Your Twitter API Key

### Step 1 — Create a Developer Account
1. Go to **https://developer.twitter.com**
2. Click **Sign up** (or Sign in if you have an existing Twitter/X account)
3. Apply for a developer account — choose **"Hobbyist" → "Exploring the API"**
4. Fill in the required details about your use case (e.g. "Building a class project scheduler")
5. Agree to the Developer Agreement and submit — approval is usually instant

### Step 2 — Create a Project and App
1. Once approved, go to the **Developer Portal dashboard**
2. Click **"+ Create Project"**, give it a name (e.g. PostFlow)
3. Select **"Student"** or **"Building personal projects"** as the use case
4. Click **"+ Create App"** inside the project, give the app a name

### Step 3 — Set App Permissions
1. Inside your app, go to the **"Settings"** tab
2. Under **"User authentication settings"**, click **Edit**
3. Set **App permissions** to **"Read and Write"** ← this is required to post tweets
4. Save the changes

### Step 4 — Get Your Bearer Token
1. Go to the **"Keys and Tokens"** tab of your app
2. Under **"Bearer Token"**, click **"Generate"** (or Regenerate)
3. **Copy the token immediately** — it won't be shown again in full
4. Store it safely (do NOT commit it to Git)

---

## 📁 Where to Put the API Key

### Option A — Streamlit secrets file (recommended)
Create a file called `.streamlit/secrets.toml` in your project folder:

```
social_scheduler/
└── .streamlit/
    └── secrets.toml   ← create this file
```

Inside `secrets.toml`:
```toml
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAxxxxxx..."
```

Then in `app.py` you can load it with:
```python
import streamlit as st
token = st.secrets["TWITTER_BEARER_TOKEN"]
```

> ⚠️ Add `.streamlit/secrets.toml` to your `.gitignore` file so your key is never pushed to GitHub.

### Option B — Settings page (session only)
Open the app, go to **⚙️ Settings**, paste your Bearer Token, and click **Save Settings**.
This works for testing but resets every time you restart the app.

---

## Error Handling

| Error type | Cause | Behaviour |
|---|---|---|
| `AuthenticationError` | Empty or invalid token | Shown immediately, not retried |
| `RateLimitError` | Too many requests | Shown immediately, not retried |
| `NetworkError` | No internet / timeout | Auto-retried up to 3 times |
| `APIError` | Other HTTP 4xx/5xx | Auto-retried up to 3 times |
| `SchedulerError` | Bad post ID / duplicate | Caught and shown in UI |
| `HistoryError` | Corrupt JSON file | Caught and shown in UI |
| `ValueError` | Empty content / past date | Caught before any API call |
