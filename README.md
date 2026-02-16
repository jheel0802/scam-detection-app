# Real-Time Scam Call Detection

A full-stack web application that analyzes phone calls in real-time to detect scam indicators, using browser microphone capture, speech-to-text with ElevenLabs, and LLM analysis with Google Gemini.

## Overview

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

## Tech Stack

- **Backend**: Python 3.8+ with FastAPI
- **Frontend**: HTML5 + JavaScript
- **Audio APIs**: 
  - Web Audio API (browser microphone)
  - ElevenLabs Speech-to-Text API
  - Google Gemini API
- **Async**: Python asyncio for non-blocking processing

## Prerequisites

- Python 3.8 or higher
- Modern web browser with microphone support
- API Keys:
  - [ElevenLabs API Key](https://elevenlabs.io/sign-up)
  - [Google Gemini API Key](https://aistudio.google.com/app/apikey)

## Quick Start

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
# Starting Scam Detection API
# Uvicorn running on http://0.0.0.0:8000
```

The backend will be available at `http://localhost:8000`


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

## API Endpoints

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

## How It Works

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

## Scam Detection Features

The system identifies:

- **Technical Support Scams**: Fake Microsoft/Apple support
- **Bank Scams**: Impersonating banks, OTP/password requests
- **IRS Scams**: Tax authority impersonation
- **Prize/Lottery Scams**: "You've won" claims
- **Love/Romance Scams**: Emotional manipulation
- **Job Scams**: Work-from-home recruitment fraud
- **Phishing**: Credential harvesting

## Testing

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


## Project Structure

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

## Configuration

### Backend Environment Variables

Edit `backend/.env`:

```ini
# API Keys
ELEVENLABS_API_KEY=xxx
GEMINI_API_KEY=xxx

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

## Performance Metrics
- **Latency**: ~2-3 seconds per chunk (including transcription and analysis)
- **Accuracy**: Depends on Gemini model and prompt quality
- **Storage**: Transcripts kept in memory (30-second window)

## License

This project is provided as-is for educational and research purposes.

## Contributing

Feel free to:
- Report bugs and issues
- Suggest improvements
- Add more scam detection patterns
- Improve UI/UX
- Add more languages

## Disclaimer

This tool is designed to help identify potential scam patterns but should not be relied upon as the sole indicator of fraudulent activity. Always:

- Verify caller identity through official channels
- Contact banks/companies directly using numbers on official accounts
- Never share sensitive information based on unsolicited calls
- Report suspected scams to authorities
- Use in conjunction with other security measures

For official scam reporting:
- **FTC**: https://reportfraud.ftc.gov/
- **IC3**: https://www.ic3.gov/

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review backend/frontend logs
3. Test API endpoints manually with curl
4. Check API key validity and quotas

---

Made with ❤️ for protecting people from scam calls.
