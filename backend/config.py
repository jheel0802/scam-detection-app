import os
from dotenv import load_dotenv

load_dotenv()

# API Keys - The backend services look for these specific names
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY", "") # Must match llm_analysis.py
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Server configuration
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def validate_config():
    missing = []
    if not ELEVENLABS_API_KEY: missing.append("ELEVENLABS_API_KEY")
    if not BACKBOARD_API_KEY: missing.append("BACKBOARD_API_KEY")
    
    if missing:
        print(f"⚠️ Missing: {', '.join(missing)}")
    return len(missing) == 0