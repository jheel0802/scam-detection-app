"""
LLM Analysis service using Backboard.io API.
Targets the Gemini 1.5 Flash model through Backboard's unified gateway.
"""
import httpx
import json
import logging
from typing import Dict, Optional
from config import BACKBOARD_API_KEY # Ensure this exists in your config.py!

logger = logging.getLogger(__name__)

# Backboard unified API endpoint (OpenAI-compatible)
BACKBOARD_URL = "https://api.backboard.io/v1/chat/completions"

async def analyze_transcript(
    transcript: str,
    context: Optional[str] = None
) -> Optional[Dict]:
    """
    Analyze transcript for scam indicators using Backboard + Gemini.
    """
    if not BACKBOARD_API_KEY:
        logger.error("Backboard API key not configured in config.py")
        return get_default_analysis()
    
    try:
        # Construct the full context
        history = f"Previous Context: {context}\n" if context else ""
        full_prompt = f"{history}New Audio Segment to Analyze: {transcript}"

        payload = {
            "model": "google/gemini-1.5-flash", # Routing to Gemini via Backboard
            "messages": [
                {
                    "role": "system", 
                    "content": (
                        "You are an elite fraud detection AI. Analyze the transcript for social engineering. "
                        "If you detect requests for 'Gift Cards', 'Crypto', 'OTP', or 'Immediate Action' "
                        "under threat, you MUST classify as HIGH risk. "
                        "Respond ONLY in valid JSON with keys: risk_level (low|medium|high), "
                        "scam_type (string), reasons (list), and confidence (0.0-1.0)."
                    )
                },
                {"role": "user", "content": full_prompt}
            ],
            "response_format": { "type": "json_object" },
            "temperature": 0.1
        }

        headers = {
            "Authorization": f"Bearer {BACKBOARD_API_KEY}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(BACKBOARD_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            # Backboard/OpenAI format: choices[0].message.content
            content = result['choices'][0]['message']['content']
            
            analysis = json.loads(content)
            
            # Simple validation/normalization
            analysis["risk_level"] = analysis.get("risk_level", "low").lower()
            analysis["scam_type"] = analysis.get("scam_type", "General Conversation")
            analysis["reasons"] = analysis.get("reasons", [])
            analysis["confidence"] = float(analysis.get("confidence", 0.0))
            
            return analysis
        else:
            logger.error(f"Backboard Error {response.status_code}: {response.text}")
            return get_default_analysis()
            
    except Exception as e:
        logger.error(f"LLM analysis error: {str(e)}")
        return get_default_analysis()

def get_default_analysis() -> Dict:
    return {
        "risk_level": "low",
        "scam_type": "Connection Issue",
        "reasons": ["Unable to reach AI analysis - check API keys"],
        "confidence": 0.0
    }