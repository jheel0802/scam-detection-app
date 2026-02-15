# 🎙️ Real-Time Scam Call Detection

A full-stack web application that analyzes phone calls in real-time to detect scam indicators, using browser microphone capture, speech-to-text with ElevenLabs, and LLM analysis with Google Gemini.

## 📋 Overview

This application provides real-time detection of common scam patterns in phone conversations:

- **Audio Capture**: Records audio from your microphone using Web Audio API
- **Speech-to-Text**: Converts audio chunks to text using ElevenLabs API
- **Context Management**: Maintains a 30-second rolling window of conversation history
- **AI Analysis**: Uses Google Gemini API via Backboard to detect scam indicators
- **Real-Time Feedback**: Displays risk levels (Low/Medium/High) with explanations

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                        │
│            - Web Audio API for microphone capture            │
│            - Real-time transcript display                    │
│            - Risk indicator with visual feedback             │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/WebSocket
┌────────────────▼────────────────────────────────────────────┐
│              Backend (FastAPI - Python)                      │
│  ┌──────────────────┬──────────────────┬─────────────────┐  │
│  │ Transcription    │ Context Manager  │ LLM Analysis    │  │
│  │ (ElevenLabs)     │ (30s rolling)    │ (Google Gemini) │  │
│  └──────────────────┴──────────────────┴─────────────────┘  │
│                                                              │
│  Endpoints:                                                  │
│  - POST /process-audio      → Transcribe audio              │
│  - POST /analyze            → Analyze for scams             │
│  - POST /process-and-analyze → Combined endpoint            │
│  - POST /reset              → Start new session             │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: Python 3.8+ with FastAPI
- **Frontend**: HTML5 + vanilla JavaScript (no dependencies)
- **Audio APIs**: 
  - Web Audio API (browser microphone)
  - ElevenLabs Speech-to-Text API
  - Google Gemini API (via Backboard)
- **Async**: Python asyncio for non-blocking processing

## 📦 Prerequisites

- Python 3.8 or higher
- Modern web browser with microphone support
- API Keys:
  - [ElevenLabs API Key](https://elevenlabs.io/sign-up)
  - [Google Gemini API Key](https://aistudio.google.com/app/apikey)

## 🚀 Quick Start

### 1. Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create a Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env

# Edit .env and add your API keys:
# - ELEVENLABS_API_KEY=your_api_key
# - GEMINI_API_KEY=your_api_key
```

**Get your API keys:**

<details>
<summary><strong>ElevenLabs API Key</strong></summary>

1. Go to https://elevenlabs.io/sign-up
2. Sign up/Login to your account
3. Navigate to API Settings: https://elevenlabs.io/app/settings/api-keys
4. Copy your API key
5. Paste it in your `.env` file as `ELEVENLABS_API_KEY=your_key_here`
</details>

<details>
<summary><strong>Google Gemini API Key</strong></summary>

1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Select or create a project
4. Copy the API key
5. Paste it in your `.env` file as `GEMINI_API_KEY=your_key_here`
</details>

### 2. Start Backend

```bash
# From backend directory (with venv activated)
python main.py

# You should see:
# 🚀 Starting Scam Detection API
# Uvicorn running on http://0.0.0.0:8000
```

The backend will be available at `http://localhost:8000`

Health check: http://localhost:8000/health

### 3. Open Frontend

```bash
# Option 1: Open directly in browser
cd ../frontend
open index.html  # macOS
# or double-click it on Windows/Linux

# Option 2: Use a local server (recommended for best compatibility)
python3 -m http.server 3000 --directory frontend
# Then visit: http://localhost:3000
```

### 4. Test the Application

1. Click **"Start Recording"** button
2. Speak some text or play a test call
3. Watch the transcript appear in real-time
4. View risk assessment with detected indicators
5. Click **"Stop Recording"** to end the call
6. Click **"Reset"** to clear and start a new call

## 📡 API Endpoints

### POST `/process-audio`
Transcribe an audio chunk.

**Request:**
```json
{
  "audio_data": "base64_encoded_audio_data",
  "chunk_id": 1
}
```

**Response:**
```json
{
  "transcript": "Hello, this is your bank calling...",
  "chunk_id": 1,
  "timestamp": 1234567890.123
}
```

### POST `/analyze`
Analyze a transcript for scam indicators.

**Request:**
```json
{
  "transcript": "Verify your account immediately",
  "context": "Previous conversation context..."
}
```

**Response:**
```json
{
  "transcript": "Verify your account immediately",
  "risk_level": "high",
  "scam_type": "bank scam",
  "reasons": [
    "Urgency detected - 'immediately'",
    "Request for account verification",
    "Impersonation of financial institution"
  ],
  "confidence": 0.95
}
```

### POST `/process-and-analyze`
Combined endpoint: transcribe audio and analyze in one request.

**Request:**
```json
{
  "audio_data": "base64_encoded_audio_data",
  "chunk_id": 1
}
```

**Response:**
```json
{
  "transcript": "Verify your account immediately",
  "risk_level": "high",
  "scam_type": "bank scam",
  "reasons": ["urgency", "request for sensitive info"],
  "chunk_id": 1,
  "timestamp": 1234567890.123
}
```

### POST `/reset`
Reset the conversation context (start new call).

**Response:**
```json
{
  "status": "ok",
  "message": "Context reset for new call"
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "scam-detection-api",
  "context_items": 5
}
```

### GET `/context`
Get current context (for debugging).

**Response:**
```json
{
  "context_text": "Full context string...",
  "transcript_count": 5,
  "transcripts": ["chunk1", "chunk2", ...]
}
```

## 🎵 How It Works

### Real-Time Audio Processing

1. **Audio Capture** (Browser)
   - Records audio in 4-second chunks
   - Uses Web Audio API with noise suppression and echo cancellation
   - Converts audio to WAV format and encodes as base64

2. **Transcription** (Backend)
   - Receives base64 audio data
   - Sends to ElevenLabs API for speech-to-text
   - Returns transcript immediately

3. **Context Management** (Backend)
   - Maintains rolling 30-second transcript history
   - Removes old transcripts automatically
   - Provides context to LLM for better analysis

4. **Scam Detection** (Backend)
   - Sends transcript + context to Google Gemini API
   - Analyzes for common scam patterns:
     - Urgency ("Act immediately", "Now", "Immediately")
     - Sensitive information requests (passwords, OTP, card numbers)
     - Financial institution impersonation
     - Threats or intimidation
     - Unusual financial requests
   - Returns risk level, scam type, and specific reasons

5. **UI Updates** (Browser)
   - Real-time transcript display
   - Live risk indicator (color-coded)
   - List of detected indicators
   - Confidence score

## 🛡️ Scam Detection Features

The system identifies:

- **Technical Support Scams**: Fake Microsoft/Apple support
- **Bank Scams**: Impersonating banks, OTP/password requests
- **IRS Scams**: Tax authority impersonation
- **Prize/Lottery Scams**: "You've won" claims
- **Love/Romance Scams**: Emotional manipulation
- **Job Scams**: Work-from-home recruitment fraud
- **Phishing**: Credential harvesting

## 🧪 Testing

### Test Cases

1. **Normal Conversation**
   - Speak natural conversation
   - Should return LOW risk

2. **Suspicious Call**
   - Say: "Hello, this is your bank. We detected suspicious activity. Verify your password immediately."
   - Should return HIGH risk with reasons

3. **Urgency Indicators**
   - Say: "Act now, your account will be closed immediately if you don't verify."
   - Should detect urgency and multi-factor triggers

### Simulate Without Speaking

You can also test by sending raw transcripts to the `/analyze` endpoint:

```bash
# From terminal:
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Verify your credit card details now or your account will be suspended"}'

# Expected: HIGH risk, reasons about urgency and financial info request
```

## 📝 Project Structure

```
scam-detection-app/
├── backend/
│   ├── main.py                      # Main FastAPI application
│   ├── config.py                    # Configuration and environment variables
│   ├── models.py                    # Pydantic data models
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Example environment file
│   └── services/
│       ├── transcription.py         # ElevenLabs integration
│       ├── llm_analysis.py          # Google Gemini integration
│       └── context_manager.py       # Rolling transcript context
│
└── frontend/
    └── index.html                   # Single-page app (HTML + JS)
```

## 🔧 Configuration

### Backend Environment Variables

Edit `backend/.env`:

```ini
# API Keys
ELEVENLABS_API_KEY=sk_xxx
GEMINI_API_KEY=AIza_xxx

# Server
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
FRONTEND_URL=http://localhost:3000
```

### Frontend Configuration

Edit these variables in `frontend/index.html`:

```javascript
const API_ENDPOINT = 'http://localhost:8000';  // Backend URL
const CHUNK_DURATION_MS = 4000;                // Audio chunk duration
const SAMPLE_RATE = 16000;                     // Audio sample rate
```

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check if port 8000 is in use
lsof -i :8000
```

### "Backend not available" error

- Ensure backend is running: `python main.py`
- Check backend logs for errors
- Verify port 8000 is accessible
- Check CORS settings in `config.py`

### Microphone not working

- Check browser permissions (Settings → Privacy)
- Use HTTPS in production (microphone requires secure context)
- Try a different browser
- Check browser console for errors (F12)

### "API Key not configured"

- Verify `.env` file exists in backend directory
- Check API keys are correctly pasted
- Restart backend after changing `.env`
- Run `python config.py` to validate keys

### ElevenLabs API errors

- Check API key is valid: https://elevenlabs.io/app/settings/api-keys
- Verify API quota isn't exceeded
- Check internet connection

### Gemini API errors

- Get fresh API key from https://aistudio.google.com/app/apikey
- Ensure API is enabled in Google Cloud Console
- Check request rate limits

## 🚀 Deployment

### Production Checklist

- [ ] Use environment variables for all secrets
- [ ] Set FRONTEND_URL to production domain
- [ ] Enable HTTPS (microphone requires secure context)
- [ ] Configure CORS properly for production domain
- [ ] Increase API rate limits and quotas
- [ ] Add request logging and monitoring
- [ ] Use production-grade server (e.g., Gunicorn)
- [ ] Add database for transcript history
- [ ] Implement user authentication

### Deploy Backend (Example: AWS EC2)

```bash
# Install dependencies
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Or use Docker
docker build -t scam-detector .
docker run -e ELEVENLABS_API_KEY=xxx -e GEMINI_API_KEY=xxx -p 8000:8000 scam-detector
```

### Deploy Frontend

- Static HTML, CSS, JS - deploy to any static host
- Vercel, Netlify, GitHub Pages, AWS S3 + CloudFront, etc.
- Update `API_ENDPOINT` in `index.html` to point to backend

## 📊 Performance Metrics

- **Latency**: ~2-3 seconds per chunk (including transcription and analysis)
- **Throughput**: Multiple concurrent users
- **Accuracy**: Depends on Gemini model and prompt quality
- **Storage**: Transcripts kept in memory (30-second window)

## 🔐 Security & Privacy

- Audio data is only sent to official APIs (ElevenLabs, Google)
- No data is stored locally (except conversation context)
- HTTPS recommended for production
- API keys should never be exposed in frontend code
- Consider implementing user authentication
- Add rate limiting for production use

## 📚 API Documentation

Full API documentation available at: `http://localhost:8000/docs` (Swagger UI)
Alternative docs at: `http://localhost:8000/redoc` (ReDoc)

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Web Audio API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- **ElevenLabs**: https://elevenlabs.io/docs
- **Google Gemini**: https://ai.google.dev/
- **Async/await**: https://python.readthedocs.io/en/latest/library/asyncio.html

## 📄 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Feel free to:
- Report bugs and issues
- Suggest improvements
- Add more scam detection patterns
- Improve UI/UX
- Add more languages

## ⚠️ Disclaimer

This tool is designed to help identify potential scam patterns but should not be relied upon as the sole indicator of fraudulent activity. Always:

- Verify caller identity through official channels
- Contact banks/companies directly using numbers on official accounts
- Never share sensitive information based on unsolicited calls
- Report suspected scams to authorities
- Use in conjunction with other security measures

For official scam reporting:
- **FTC**: https://reportfraud.ftc.gov/
- **FBI**: https://www.fbi.gov/contact-us/its/white-collar-crime/internet-fraud-complaint-center
- **IC3**: https://www.ic3.gov/

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review backend/frontend logs
3. Test API endpoints manually with curl
4. Check API key validity and quotas

---

Made with ❤️ for protecting people from scam calls.
