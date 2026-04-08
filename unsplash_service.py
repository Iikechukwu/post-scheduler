import requests
import streamlit as st

class UnsplashService:
    def __init__(self):
        self.access_key = st.secrets.get("UNSPLASH_ACCESS_KEY", "")
        self.base_url = "https://api.unsplash.com/search/photos"

    def fetch_image(self, query):
        if not self.access_key:
            return "https://via.placeholder.com/800x400?text=Missing+API+Key"
        
        try:
            params = {"query": query, "client_id": self.access_key, "per_page": 1}
            response = requests.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return data['results'][0]['urls']['regular']
            return "https://via.placeholder.com/800x400?text=No+Results+Found"
        except Exception:
            return "https://via.placeholder.com/800x400?text=API+Error"