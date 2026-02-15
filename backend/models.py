"""
Data models for requests and responses.
"""
from pydantic import BaseModel
from typing import List, Optional


class TranscriptRequest(BaseModel):
    """Request model for audio processing."""
    audio_data: str  # Base64 encoded audio data
    chunk_id: int  # Chunk identifier for tracking


class TranscriptResponse(BaseModel):
    """Response model for transcription."""
    transcript: str
    chunk_id: int
    timestamp: float


class AnalysisRequest(BaseModel):
    """Request model for scam analysis."""
    transcript: str
    context: Optional[str] = None  # Previous transcripts for context


class AnalysisResponse(BaseModel):
    """Response model for scam analysis with structured data."""
    risk_level: str  # "low", "medium", or "high"
    scam_type: Optional[str]  # Type of scam detected, if any
    reasons: List[str]  # List of reasons for risk assessment
    confidence: float  # Confidence score 0.0-1.0
    transcript: str  # Echo back the analyzed transcript


class ScamDetectionResult(BaseModel):
    """Combined result model for real-time updates."""
    transcript: str
    risk_level: str
    scam_type: Optional[str]
    reasons: List[str]
    chunk_id: int
    timestamp: float
