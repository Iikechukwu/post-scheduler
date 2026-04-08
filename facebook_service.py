import requests
import streamlit as st
import os

class FacebookService:
    def __init__(self):
        self.access_token = st.secrets.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        self.page_id = st.secrets.get("FACEBOOK_PAGE_ID", "")
        self.user_access_token = st.secrets.get("FACEBOOK_USER_ACCESS_TOKEN", "")
        self.base_url = "https://graph.facebook.com/v22.0"

    def get_page_token_from_user_token(self):
        """
        Exchange user token for page token if not stored.
        Returns: (page_id, page_access_token) or (None, None) on error
        """
        if not self.user_access_token:
            return None, None
        
        try:
            url = f"{self.base_url}/me/accounts"
            response = requests.get(url, params={"access_token": self.user_access_token}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get("data", [])
                if accounts:
                    page = accounts[0]  # Use first page
                    return page.get("id"), page.get("access_token")
            return None, None
        except:
            return None, None

    def post_to_feed(self, caption, image_url=None):
        """
        Post to Facebook Page feed.
        Returns: (success: bool, post_id: str or None, error: str or None)
        """
        # Try to use stored page token, fall back to fetching from user token
        page_id = self.page_id
        page_token = self.access_token
        
        if not page_token or not page_id:
            # Try to get page info from user token
            page_id, page_token = self.get_page_token_from_user_token()
        
        if not page_token or not page_id:
            return False, None, "Missing FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID in secrets. Alternatively, provide FACEBOOK_USER_ACCESS_TOKEN to fetch page token."

        try:
            response = None
            if image_url:
                endpoint = f"{self.base_url}/{page_id}/photos"
                # Facebook accepts either a public URL or an uploaded binary file.
                if isinstance(image_url, str) and image_url.lower().startswith(("http://", "https://")):
                    payload = {
                        "url": image_url,
                        "caption": caption,
                        "access_token": page_token
                    }
                    response = requests.post(endpoint, data=payload, timeout=10)
                else:
                    local_path = image_url
                    if isinstance(image_url, str) and not os.path.exists(local_path):
                        local_path = os.path.join(os.getcwd(), image_url)

                    if os.path.exists(local_path):
                        payload = {
                            "caption": caption,
                            "access_token": page_token
                        }
                        with open(local_path, "rb") as f:
                            response = requests.post(endpoint, data=payload, files={"source": f}, timeout=20)
                    else:
                        # If image path is invalid, fallback to text-only post instead of failing.
                        endpoint = f"{self.base_url}/{page_id}/feed"
                        payload = {
                            "message": caption,
                            "access_token": page_token
                        }
                        response = requests.post(endpoint, data=payload, timeout=10)
            else:
                endpoint = f"{self.base_url}/{page_id}/feed"
                payload = {
                    "message": caption,
                    "access_token": page_token
                }
                response = requests.post(endpoint, data=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                data = response.json()
                post_id = data.get("id")
                return True, post_id, None
            else:
                error_msg = f"Facebook API error {response.status_code}: {response.text}"
                return False, None, error_msg
        
        except Exception as e:
            return False, None, f"Exception posting to Facebook: {str(e)}"
