"""
Transcription service using ElevenLabs Speech-to-Text API.
"""
import httpx
import base64
import logging
from typing import Optional
from config import ELEVENLABS_API_KEY

logger = logging.getLogger(__name__)

# ElevenLabs API endpoint for speech-to-text
ELEVENLABS_STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"


async def transcribe_audio(audio_data_base64: str) -> Optional[str]:
    """
    Send audio chunk to ElevenLabs for transcription.
    
    Args:
        audio_data_base64: Base64 encoded audio data
    
    Returns:
        Transcribed text or None if transcription fails
    """
    if not ELEVENLABS_API_KEY:
        logger.error("ElevenLabs API key not configured")
        return None
    
    if len(audio_data_base64) < 500: 
        logger.warning("Chunk too small, skipping transcription.")
        return "" # Return empty string instead of crashing
    
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data_base64)
        
        # Prepare request headers
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY.strip(),  # Remove any whitespace
        }
        
        # Prepare form data - ElevenLabs expects file in form data
        files = {
            "file": ("audio.wav", audio_bytes, "audio/wav")
        }
        data = {
            "model_id": "scribe_v2",  # Latest ElevenLabs speech-to-text model
            "language_code": "en"
        }
        
        logger.debug(f"Sending transcription request to {ELEVENLABS_STT_URL}")
        logger.debug(f"Audio size: {len(audio_bytes)} bytes")
        
        # Send audio to ElevenLabs
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ELEVENLABS_STT_URL,
                headers=headers,
                files=files,
                data=data
            )
        
        logger.debug(f"ElevenLabs response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            transcript = result.get("text", "")
            logger.info(f"✅ Transcribed: {transcript[:50]}...")
            return transcript
        else:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = str(error_json)
            except:
                pass
            
            logger.error(f"ElevenLabs API error {response.status_code}:")
            logger.error(f"  Response: {error_detail}")
            
            # Check if it's an authentication error
            if response.status_code == 401 or response.status_code == 403:
                logger.error("❌ Authentication failed - check your API key!")
                logger.error("   ElevenLabs keys should start with 'xi_'")
                logger.error("   Get your key from: https://elevenlabs.io/app/settings/api-keys")
            
            return None
            
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        logger.error(f"  This could mean:")
        logger.error(f"  1. Invalid API key")
        logger.error(f"  2. Network connection issue")
        logger.error(f"  3. ElevenLabs API is down")
        return None


async def validate_audio_format(audio_data_base64: str) -> bool:
    """
    Validate that audio data is properly formatted.
    
    Args:
        audio_data_base64: Base64 encoded audio data
    
    Returns:
        True if valid, False otherwise
    """
    try:
        base64.b64decode(audio_data_base64)
        return True
    except Exception:
        return False
