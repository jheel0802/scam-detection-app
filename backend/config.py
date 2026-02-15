import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Server configuration
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def validate_config():
    missing = []
    if not ELEVENLABS_API_KEY: missing.append("ELEVENLABS_API_KEY")
    if not GEMINI_API_KEY: missing.append("GEMINI_API_KEY")
    
    if missing:
        print(f"⚠️ Missing: {', '.join(missing)}")
    return len(missing) == 0