

# app/config.py
import os
from dotenv import load_dotenv
load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not N8N_WEBHOOK_URL:
    raise RuntimeError("N8N_WEBHOOK_URL is not set")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not set")
