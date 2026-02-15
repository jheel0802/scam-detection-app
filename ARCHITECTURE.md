# 📚 Architecture & Implementation Guide

This document explains the architecture and key components of the Scam Detection system.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Browser (Client)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Web Audio API                                    │  │
│  │ - Captures microphone input                      │  │
│  │ - Splits into 4-second chunks                    │  │
│  │ - Converts to WAV format                         │  │
│  │ - Encodes to Base64                             │  │
│  └──────────────────────────────────────────────────┘  │
│                        ↓ HTTP POST                      │
└─────────────────────────────────────────────────────────┘
                        │
                        │ JSON payload:
                        │ {
                        │   "audio_data": "base64...",
                        │   "chunk_id": 1
                        │ }
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│                 FastAPI Backend                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ /process-and-analyze Endpoint                    │  │
│  │ (async request handler)                          │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                    ↓        │
│    ┌──────────────┐              ┌───────────────────┐ │
│    │TRANSCRIPTION │              │ CONTEXT MANAGER   │ │
│    │SERVICE       │              │                   │ │
│    │              │              │ Rolling 30 sec    │ │
│    │1. Decode     │              │ transcript window │ │
│    │   base64     │              │                   │ │
│    │2. Send to    │              │ Functions:        │ │
│    │   ElevenLabs │              │ - add_transcript()│ │
│    │3. Return     │              │ - get_context()   │ │
│    │   transcript │              │                   │ │
│    └──────────────┘              └───────────────────┘ │
│           │                               │             │
│           └─────────────────┬─────────────┘             │
│                             ↓                           │
│                    ┌─────────────────┐                  │
│                    │ LLM ANALYSIS    │                  │
│                    │ SERVICE         │                  │
│                    │                 │                  │
│                    │ Using Gemini:   │                  │
│                    │ 1. Combine      │                  │
│                    │    transcript   │                  │
│                    │    + context    │                  │
│                    │ 2. Send prompt  │                  │
│                    │ 3. Parse JSON   │                  │
│                    │    response     │                  │
│                    └─────────────────┘                  │
│                          ↓                              │
│                  ┌─────────────────┐                    │
│                  │ Structured Data │                    │
│                  │ {               │                    │
│                  │   risk_level    │                    │
│                  │   scam_type     │                    │
│                  │   reasons[]     │                    │
│                  │   confidence    │                    │
│                  │ }               │                    │
│                  └─────────────────┘                    │
└─────────────────────────────────────────────────────────┘
                        ↑ HTTP Response
                        │ JSON result
                        │
┌─────────────────────────────────────────────────────────┐
│              Browser UI Update                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ - Display transcript in real-time                │  │
│  │ - Show risk level (LOW/MEDIUM/HIGH)              │  │
│  │ - Color-code indicator                           │  │
│  │ - List detected indicators                       │  │
│  │ - Show confidence score                          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Backend Components

### 1. **main.py** - FastAPI Application

The core application that exposes REST endpoints.

**Key Features:**
- CORS middleware for cross-origin requests
- Async request handlers
- Error handling and validation
- Automatic API documentation (Swagger UI)

**Main Endpoints:**
```python
@app.post("/process-and-analyze")
async def process_and_analyze(request: TranscriptRequest)
    # Main endpoint combining:
    # 1. Audio transcription
    # 2. Context management
    # 3. LLM analysis
    # Returns: ScamDetectionResult
```

**Request Flow:**
```
Client sends audio
    ↓
/process-and-analyze endpoint receives it
    ↓
Validate audio format (base64 decode check)
    ↓
transcribe_audio() → ElevenLabs API
    ↓
Add to context_manager for history
    ↓
analyze_transcript() → Gemini API
    ↓
Return structured result
    ↓
Client receives and displays result
```

### 2. **services/transcription.py** - Speech-to-Text

Handles audio transcription using ElevenLabs API.

```python
async def transcribe_audio(audio_data_base64: str) -> Optional[str]
    # Steps:
    # 1. Decode base64 to raw audio bytes
    # 2. Call ElevenLabs STT API
    # 3. Extract and return transcript text
    
# Error Handling:
# - Validates API key exists
# - Handles network errors
# - Returns None if transcription fails
# - Logs all errors for debugging
```

**API Integration:**
```
ElevenLabs Endpoint: https://api.elevenlabs.io/v1/speech-to-text
Method: POST
Headers: xi-api-key: {ELEVENLABS_API_KEY}
Body: Raw audio bytes (WAV format)
Response: JSON with "text" field
```

### 3. **services/llm_analysis.py** - Scam Detection

Analyzes transcripts for scam indicators using Gemini.

```python
async def analyze_transcript(
    transcript: str,
    context: Optional[str] = None
) -> Optional[Dict]
    # Steps:
    # 1. Build analysis prompt
    # 2. Include transcript + context
    # 3. Call Gemini API
    # 4. Parse JSON response
    # 5. Return structured analysis
```

**Gemini Prompt Structure:**
```
"Analyze phone call transcript for scam indicators.

Transcript:
[Current transcript + previous context]

Common scam indicators:
- Urgency
- Request for sensitive info
- Impersonation
- Threats
- Unusual financial requests
- Grammar issues

Return JSON with:
{
  'risk_level': 'low|medium|high',
  'scam_type': 'type or null',
  'reasons': ['list', 'of', 'reasons'],
  'confidence': 0.0-1.0
}"
```

**Scam Pattern Detection:**
The prompt trains Gemini to identify:

| Indicator | Examples |
|-----------|----------|
| **Urgency** | "immediately", "now", "right away", "act fast" |
| **Info Request** | "password", "OTP", "card number", "SSN", "PIN" |
| **Impersonation** | "bank", "government", "IRS", "Microsoft", "Apple" |
| **Threats** | "close your account", "arrest you", "fine", "consequences" |
| **Financial** | "wire transfer", "gift cards", "payment", "send money" |
| **Suspicious Language** | Grammar errors, accent mismatches, scripted dialogue |

### 4. **services/context_manager.py** - History Management

Maintains a rolling window of recent transcripts.

```python
class TranscriptContext:
    def __init__(self, window_seconds=30):
        self.window_seconds = 30  # 30-second window
        self.transcripts = deque(maxlen=10)  # Max 10 chunks
        
    def add_transcript(text: str):
        # Add new transcript chunk
        # Automatically removes oldest if at max
        
    def get_context() -> str:
        # Returns all transcripts within time window
        # Used for LLM analysis to understand conversation
        
    def clear():
        # Reset for new call
```

**Why Context Matters:**
- **Better Detection**: Gemini understands conversation flow
- **Patterns**: Multi-step scams become visible
- **Accuracy**: Context reduces false positives
- **Example**: 
  - Chunk 1: "Hello, this is your bank"
  - Chunk 2: "We need to verify your password"  ← HIGH risk when seen together

### 5. **models.py** - Data Models

Pydantic models for request/response validation.

```python
# Request Models
TranscriptRequest
    audio_data: str (base64)
    chunk_id: int

AnalysisRequest
    transcript: str
    context: Optional[str]

# Response Models
TranscriptResponse
    transcript: str
    chunk_id: int
    timestamp: float

AnalysisResponse
    transcript: str
    risk_level: str ("low", "medium", "high")
    scam_type: Optional[str]
    reasons: List[str]
    confidence: float (0.0-1.0)

ScamDetectionResult
    (combines transcription + analysis)
```

### 6. **config.py** - Configuration

Environment variable management.

```python
# Loads from .env file
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))

# Validation
def validate_config():
    # Checks all required keys are set
    # Warns if missing
```

## Frontend Components

### index.html - Single Page Application

```
┌─────────────────────────────────┐
│  DOM Elements                   │
│  ├─ startBtn                    │
│  ├─ stopBtn                     │
│  ├─ resetBtn                    │
│  ├─ transcriptBox               │
│  ├─ riskLevel                   │
│  ├─ reasonsList                 │
│  └─ statusBox                   │
└─────────────────────────────────┘
          ↑↓
┌─────────────────────────────────┐
│  JavaScript State               │
│  ├─ audioContext (Web Audio)    │
│  ├─ mediaStream (microphone)    │
│  ├─ mediaRecorder (recorder)    │
│  ├─ isRecording (boolean)       │
│  └─ chunkCount (number)         │
└─────────────────────────────────┘
```

### Recording Flow

```javascript
START RECORDING
    ↓
    navigator.mediaDevices.getUserMedia()
        ↓ (waits for user permission)
    MediaRecorder starts
        ↓
    Every 4 seconds: chunk of audio
        ↓
    Convert WAV → Base64
        ↓
    POST to /process-and-analyze
        ↓
    Receive result
        ↓
    UPDATE DOM:
    - Add transcript chunk
    - Update risk indicator
    - Update reasons list
        ↓
    REPEAT until STOP clicked
```

### Audio Processing

```javascript
// Web Audio API Flow
navigator.mediaDevices.getUserMedia()
    ↓
    MediaRecorder (records audio)
    ↓
    ondataavailable event (every 1000ms)
    ↓
    Accumulate chunks for 4 seconds
    ↓
    Blob → ArrayBuffer
    ↓
    audioContext.decodeAudioData()
    ↓
    AudioBuffer (raw PCM data)
    ↓
    Convert to WAV (WavEncoder class)
    ↓
    Base64 encode
    ↓
    Send to backend
```

### WavEncoder Class

Custom WAV file encoder in JavaScript:
```javascript
class WavEncoder {
    encode(channels)     // Input: Float32Array
        ↓
    finish()             // Output: Blob (WAV file)
}

// Steps:
// 1. Create ArrayBuffer for WAV file
// 2. Write RIFF header (WAV format spec)
// 3. Write "fmt " chunk (audio format info)
// 4. Write "data" chunk (raw PCM data)
// 5. Convert Int16 samples with volume scaling
// 6. Return as Blob
```

## Data Flow Examples

### Example 1: Normal Conversation

```
User speaks: "Hi, what time is it?"

→ Audio recorded and sent to backend

→ ElevenLabs: "Hi, what time is it?"

→ Gemini analysis:
   - No urgency
   - No info request
   - Normal greeting
   
→ Result:
   risk_level: "low"
   scam_type: null
   reasons: ["Normal conversation, no indicators detected"]
   confidence: 0.95
```

### Example 2: Suspected Bank Scam

```
User hears: "This is your bank. Verify your password now or account will close."

→ Audio recorded (2 chunks) and sent

→ ElevenLabs chunk 1: "This is your bank"
→ ElevenLabs chunk 2: "Verify your password now or account will close"

→ Context = "This is your bank Verify your password now..."

→ Gemini analysis on chunk 2 with full context:
   - Impersonation detected (bank)
   - Urgency detected (now)
   - Sensitive info request (password)
   - Threat detected (account will close)
   
→ Result:
   risk_level: "high"
   scam_type: "bank impersonation scam"
   reasons: [
     "Bank impersonation detected",
     "Urgent language: 'now'",
     "Request for sensitive password",
     "Account threat: 'will close'"
   ]
   confidence: 0.99
```

### Example 3: Multi-chunk Context

```
Chunk 1: "Hello, I'm calling about your vehicle warranty"
Chunk 2: "Your warranty is expiring"
Chunk 3: "We need your credit card to renew it"

→ After chunk 3, context includes all 3 chunks

→ Gemini sees full pattern:
   - Unsolicited call
   - Warranty (common scam vector)
   - Financial information request
   - Context shows escalation pattern
   
→ Result:
   risk_level: "high"
   scam_type: "vehicle warranty scam"
   confidence: 0.92
```

## Error Handling Strategy

### Backend Error Handling

```python
try:
    audio_base64 = validate format
    transcript = await transcribe_audio()  # External API
    context_manager.add_transcript()
    analysis = await analyze_transcript()  # External API
    return result
except HTTPException:
    raise  # Already formatted
except Exception as e:
    log error
    return 500 with error message
```

### Frontend Error Handling

```javascript
try {
    response = await fetch(API_ENDPOINT)
    if (!response.ok)
        throw Error(response.json().detail)
    result = await response.json()
    updateUI(result)
} catch (error) {
    log error
    updateStatus(error.message, 'error')
    startBtn.disabled = false
}
```

## Performance Optimizations

### Backend
- **Async/await**: Non-blocking API calls
- **Context window**: Only keep last 30s (memory efficient)
- **Chunk processing**: 4-sec chunks for continuous stream
- **Error recovery**: Graceful fallback if API fails

### Frontend
- **Local audio processing**: Only send audio to backend
- **Chunked uploads**: Don't wait for entire recording
- **DOM updates**: Only update changed elements
- **Debouncing**: Don't send duplicate requests

## Testing & Debugging

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Direct analysis (no audio needed)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Verify your credit card or account closes"}'

# Debug context
curl http://localhost:8000/context

# Reset session
curl -X POST http://localhost:8000/reset
```

### Debug Logs

Backend logs show:
```
Processing audio chunk 1
Sending to ElevenLabs...
Transcribed: "Hello this is your bank..."
Added transcript to context
Analyzing transcript...
Analysis complete: high risk
Results: bank scam, 3 reasons, 0.95 confidence
```

Frontend console shows:
```
[ScamDetection] Recording started
[ScamDetection] Sending audio chunk 1 for processing...
[ScamDetection] Chunk 1 processed: Hello this is your bank
[ScamDetection] Risk: high, Type: bank scam
```

## Deployment Considerations

### Scalability
- API Gateway for rate limiting
- Kubernetes for horizontal scaling
- Redis for shared context across instances
- Load balancer for multiple backend instances

### Security
- API key rotation
- HTTPS in production (microphone requires secure context)
- Input validation (already in Pydantic models)
- Rate limiting per user/IP
- User authentication

### Monitoring
- Log aggregation (CloudWatch, ELK, etc.)
- Error tracking (Sentry, etc.)
- Performance monitoring (APM)
- Audit logs for compliance

## Code Organization Principles

1. **Separation of Concerns**
   - Services handle single responsibility
   - Models define contracts
   - Main.py orchestrates

2. **Async-first Design**
   - All external API calls are async
   - No blocking operations in request handlers
   - Database calls would be async in production

3. **Error Handling**
   - Try/catch with specific exceptions
   - Logging at all critical points
   - Graceful degradation for API failures

4. **Type Hints**
   - Pydantic for runtime validation
   - Python type hints for clarity
   - IDE autocomplete support

5. **Documentation**
   - Docstrings explain logic
   - Comments for complex sections
   - Clear variable names

---

This architecture is designed to be:
- **Simple**: Easy to understand and modify
- **Modular**: Add new services without changing others
- **Scalable**: Can handle multiple concurrent calls
- **Reliable**: Graceful error handling
- **Fast**: Optimized async operations
