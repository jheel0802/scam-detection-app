"""
Main FastAPI application for real-time scam call detection.

Endpoints:
- POST /process-audio: Transcribe audio chunk
- POST /analyze: Analyze transcript for scam indicators
- GET /health: Health check
"""
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import Optional
import base64
from contextlib import asynccontextmanager

from config import FRONTEND_URL, validate_config
from models import (
    TranscriptRequest, TranscriptResponse, 
    AnalysisRequest, AnalysisResponse,
    ScamDetectionResult
)
from services.transcription import transcribe_audio, validate_audio_format
from services.llm_analysis import analyze_transcript, get_default_analysis
from services.context_manager import get_context_manager
from services.backboard_llm_analysis import initialize_backboard_analyzer, get_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure CORS
origins = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

# Global context manager (for transcripts)
context_manager = get_context_manager()

# Global session tracker - tracks active conversation threads
active_sessions = {}  # session_id -> thread_id


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle (startup and shutdown events).
    """
    # Startup event
    logger.info("🚀 Starting Scam Detection API")
    logger.info(f"CORS enabled for: {', '.join(origins)}")
    
    # Validate API keys are configured
    if not validate_config():
        logger.warning("⚠️  API keys not fully configured. Some features may not work.")
    
    # Initialize Backboard analyzer (RAG for scam patterns)
    logger.info("🔄 Initializing Backboard Scam Analyzer (RAG)...")
    backboard_initialized = await initialize_backboard_analyzer()
    if backboard_initialized:
        logger.info("✅ Backboard analyzer initialized successfully!")
        logger.info("   Threads will be created per conversation")
    else:
        logger.warning("⚠️  Backboard analyzer initialization failed. Using Gemini fallback.")
    
    yield  # Application runs
    
    # Shutdown event (clean up if needed)
    logger.info("🛑 Shutting down Scam Detection API")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Scam Detection API",
    description="Real-time detection of scam indicators in phone calls",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    """
    Handle CORS preflight requests.
    """
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "ok",
        "service": "scam-detection-api",
        "context_items": len(context_manager)
    }


@app.post("/process-audio")
async def process_audio(
    request: TranscriptRequest
) -> TranscriptResponse:
    """
    Process audio chunk and return transcript.
    
    Args:
        request: TranscriptRequest with base64 encoded audio
    
    Returns:
        TranscriptResponse with transcribed text
    """
    try:
        logger.info(f"Processing audio chunk {request.chunk_id}")
        
        # Validate audio format
        if not await validate_audio_format(request.audio_data):
            raise HTTPException(
                status_code=400,
                detail="Invalid audio data format"
            )
        
        # Call ElevenLabs transcription service
        transcript = await transcribe_audio(request.audio_data)
        
        if transcript is None:
            raise HTTPException(
                status_code=503,
                detail="Transcription service unavailable"
            )
        
        # Add to context for future analysis
        context_manager.add_transcript(transcript)
        
        logger.info(f"Chunk {request.chunk_id} transcribed: {transcript[:50]}...")
        
        return TranscriptResponse(
            transcript=transcript,
            chunk_id=request.chunk_id,
            timestamp=asyncio.get_event_loop().time()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Audio processing failed: {str(e)}"
        )


@app.post("/analyze")
async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze transcript for scam indicators using Backboard RAG.
    
    If session_id is provided:
    - First chunk of session: Creates new thread
    - Subsequent chunks: Uses existing thread (maintains context)
    
    Args:
        request: AnalysisRequest with transcript, optional session_id and context
    
    Returns:
        AnalysisResponse with risk assessment
    """
    try:
        logger.info(f"Analyzing transcript: {request.transcript[:50]}...")
        
        if not request.transcript.strip():
            raise HTTPException(
                status_code=400,
                detail="Transcript cannot be empty"
            )
        
        analyzer = get_analyzer()
        
        # Determine if this is a new conversation or continuation
        session_id = request.session_id if hasattr(request, 'session_id') else None
        
        if session_id:
            # Check if we already have a thread for this session
            if session_id not in active_sessions:
                # NEW CONVERSATION - Create new thread
                logger.info(f"🎯 New session {session_id} - Creating new thread")
                thread_id = await analyzer.create_thread_for_chunk()
                if thread_id:
                    active_sessions[session_id] = thread_id
                    logger.info(f"✅ Thread created for session {session_id}: {thread_id}")
                else:
                    logger.error(f"Failed to create thread for session {session_id}")
                    raise HTTPException(status_code=500, detail="Failed to create conversation thread")
            else:
                # CONTINUATION - Use existing thread
                thread_id = active_sessions[session_id]
                logger.info(f"📍 Continuing session {session_id} with thread {thread_id}")
        else:
            # No session tracking - use current thread
            thread_id = analyzer.get_current_thread()
            if not thread_id:
                logger.warning("No session ID provided and no active thread - creating new one")
                thread_id = await analyzer.create_thread_for_chunk()
        
        # Send message to thread and get analysis
        response = await analyzer.send_message_to_thread(thread_id, request.transcript)
        
        if response is None:
            logger.warning("Failed to get response from Backboard, using Gemini fallback")
            # Fallback to Gemini
            context = request.context or context_manager.get_context()
            analysis = await analyze_transcript(
                request.transcript,
                context if context != request.transcript else None
            )
            if analysis is None:
                analysis = get_default_analysis()
        else:
            # Parse response from Backboard
            import json
            try:
                analysis = json.loads(response)
                print(analysis)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse Backboard response as JSON, parsing text: {response[:100]}")
                analysis = {
                    "risk_level": "unknown",
                    "scam_type": "Unable to parse response",
                    "reasons": [response],
                    "confidence": 0.0
                }
        
        logger.info(f"Analysis result: {analysis['risk_level']} risk")
        
        return AnalysisResponse(
            transcript=request.transcript,
            risk_level=analysis['risk_level'],
            scam_type=analysis.get('scam_type'),
            reasons=analysis.get('reasons', []),
            confidence=analysis.get('confidence', 0.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing transcript: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/process-and-analyze")
async def process_and_analyze(
    request: TranscriptRequest
) -> ScamDetectionResult:
    """
    Combined endpoint: transcribe audio and analyze using Backboard RAG.
    
    Thread management:
    - First chunk of call: Creates new thread
    - Subsequent chunks: Uses same thread (maintains conversation context)
    - Each chunk_id is tracked to identify conversation flow
    
    Args:
        request: TranscriptRequest with audio data and chunk_id
    
    Returns:
        ScamDetectionResult with transcript and analysis
    """
    try:
        logger.info(f"Processing and analyzing chunk {request.chunk_id}")
        
        # Step 1: Transcribe audio
        if not await validate_audio_format(request.audio_data):
            raise HTTPException(status_code=400, detail="Invalid audio format")
        
        transcript = await transcribe_audio(request.audio_data)
        if transcript is None:
            raise HTTPException(status_code=503, detail="Transcription failed")
        
        logger.info(f"Chunk {request.chunk_id} transcribed: {transcript[:50]}...")
        
        # Step 2: Determine if new conversation or continuation
        # Using session_id and chunk_id to detect conversation flow
        
        analyzer = get_analyzer()
        session_id = request.session_id
        
        if session_id and session_id not in active_sessions:
            # NEW CONVERSATION - Create new thread
            logger.info(f"🎯 New session {session_id} - Creating new thread")
            thread_id = await analyzer.create_thread_for_chunk()
            if thread_id:
                active_sessions[session_id] = thread_id
                logger.info(f"✅ Thread created for session {session_id}")
            else:
                raise HTTPException(status_code=500, detail="Failed to create thread")
        elif session_id and session_id in active_sessions:
            # CONTINUATION - Use existing thread
            thread_id = active_sessions[session_id]
            logger.info(f"📍 Continuing session {session_id}")
        else:
            # Fallback: use chunk_id
            if request.chunk_id == 1:
                thread_id = await analyzer.create_thread_for_chunk()
                if thread_id:
                    active_sessions['default'] = thread_id  # Store with 'default' key
                logger.info("🎯 New call (chunk_id=1) - Creating thread")
            else:
                thread_id = active_sessions.get('default') or analyzer.get_current_thread()
                logger.info(f"📍 Continuing (chunk_id={request.chunk_id})")
        
        # Add to context manager (for fallback analysis)
        context_manager.add_transcript(transcript)
        
        # Step 3: Analyze for scams using Backboard thread
        response = await analyzer.send_message_to_thread(thread_id, transcript)
        
        if response is None:
            logger.warning("Failed to get response from Backboard, falling back to Gemini")
            # Fallback to Gemini if Backboard fails
            context = context_manager.get_context()
            analysis = await analyze_transcript(transcript, context)
            if analysis is None:
                analysis = get_default_analysis()
        else:
            # Parse response from Backboard
            import json
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse Backboard response, falling back to Gemini")
                context = context_manager.get_context()
                analysis = await analyze_transcript(transcript, context)
                if analysis is None:
                    analysis = get_default_analysis()
        
        logger.info(f"Complete analysis: {analysis['risk_level']} risk")
        
        return ScamDetectionResult(
            transcript=transcript,
            risk_level=analysis['risk_level'],
            scam_type=analysis.get('scam_type'),
            reasons=analysis.get('reasons', []),
            chunk_id=request.chunk_id,
            timestamp=asyncio.get_event_loop().time()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in combined processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.post("/reset")
async def reset_session():
    """Reset and clear active sessions."""
    active_sessions.clear()
    context_manager.clear()
    logger.info("🔄 Session reset")
    return {"status": "ok", "message": "Session reset"}


@app.get("/context")
async def get_context():
    """
    Get the current context (for debugging).
    """
    return {
        "context_text": context_manager.get_context(),
        "transcript_count": len(context_manager),
        "transcripts": context_manager.get_all_transcripts()
    }


# --- AI CAPTCHA ENDPOINT ---
from fastapi import Body
from typing import Dict

@app.post("/captcha-verify")
async def captcha_verify(payload: Dict = Body(...)):
    """
    Accepts base64 audio, transcribes, sends to Gemini to check for human actions (e.g., [clapping], [tapping]).
    Returns {likely_human: bool, transcript: str, details: str}
    """
    audio_data = payload.get("audio_data")
    if not audio_data:
        raise HTTPException(status_code=400, detail="Missing audio_data")

    # 1. Transcribe audio
    transcript = await transcribe_audio(audio_data)
    if transcript is None:
        return {"likely_human": False, "transcript": "", "details": "Transcription failed"}

    # 2. Ask Gemini if transcript contains human actions
    prompt = (
        "You are an AI captcha verifier. The following is a transcript of a user's audio response. "
        "If the transcript contains clear evidence of human actions such as [clapping], [tapping], [snapping], [knocking], or similar, respond with JSON: {\"likely_human\": true, \"reason\": \"what action was detected\"}. "
        "If not, respond with {\"likely_human\": false, \"reason\": \"no human action detected\"}. "
        "Transcript: " + transcript
    )
    from services.llm_analysis import analyze_transcript, get_default_analysis
    # We'll use analyze_transcript but override the prompt for this special case
    import httpx, json
    from config import GEMINI_API_KEY
    GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    payload_gemini = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
    }
    headers = {"Content-Type": "application/json"}
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload_gemini, headers=headers)
        if response.status_code == 200:
            result = response.json()
            content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                verdict = json.loads(json_match.group())
                return {
                    "likely_human": verdict.get("likely_human", False),
                    "transcript": transcript,
                    "details": verdict.get("reason", "No reason returned")
                }
        return {"likely_human": False, "transcript": transcript, "details": "LLM error or unrecognized response"}
    except Exception as e:
        return {"likely_human": False, "transcript": transcript, "details": f"Exception: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    from config import BACKEND_HOST, BACKEND_PORT
    
    uvicorn.run(
        app,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        log_level="info"
    )

