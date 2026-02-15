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
]

# Global context manager (for transcripts)
context_manager = get_context_manager()


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
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    Analyze transcript for scam indicators.
    
    Args:
        request: AnalysisRequest with transcript and optional context
    
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
        
        # Use full context or provided context
        context = request.context or context_manager.get_context()
        
        # Call Gemini LLM for analysis
        analysis = await analyze_transcript(
            request.transcript,
            context if context != request.transcript else None
        )
        
        if analysis is None:
            # Return default safe analysis if API fails
            analysis = get_default_analysis()
        
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
    Combined endpoint: process audio and analyze in one request.
    Combines transcription and analysis for real-time detection.
    
    Args:
        request: TranscriptRequest with audio data
    
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
        
        # Add to context
        context_manager.add_transcript(transcript)
        
        # Step 2: Analyze for scams
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
    """
    Reset the transcript context (start a new call).
    """
    context_manager.clear()
    logger.info("Session reset - context cleared")
    return {"status": "ok", "message": "Context reset for new call"}


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


if __name__ == "__main__":
    import uvicorn
    from config import BACKEND_HOST, BACKEND_PORT
    
    uvicorn.run(
        app,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        log_level="info"
    )
