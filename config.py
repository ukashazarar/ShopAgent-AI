import os
from dotenv import load_dotenv
import streamlit as st
load_dotenv()

# SERP_API_KEY = os.getenv("SERP_API_KEY", "")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")



SERP_API_KEY = st.secrets.get("SERP_API_KEY") or os.getenv("SERP_API_KEY", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "")

TRUSTED_DOMAINS = {
    "amazon.in":       10,
    "amazon.com":      10,
    "flipkart.com":    10,
    "reliancedigital.in": 9,
    "croma.com":       9,
    "vijaysales.com":  8,
    "bestbuy.com":     10,
    "walmart.com":     10,
    "ebay.com":        7,
    "snapdeal.com":    7,
    "tatacliq.com":    8,
    "myntra.com":      8,
    "paytmmall.com":   7,
    "shopclues.com":   6,
}

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 3
REQUEST_TIMEOUT = 12
