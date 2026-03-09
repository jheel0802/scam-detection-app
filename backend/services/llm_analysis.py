# """LLM Analysis service using Google Gemini API.
# Analyzes transcripts for scam indicators.

# TODO: Integrate Backboard.io for conversation persistence later
# """
# import httpx
# import json
# import logging
# from typing import Dict, Optional
# from config import GEMINI_API_KEY

# logger = logging.getLogger(__name__)

# # Google Gemini API
# GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# async def analyze_transcript(
#     transcript: str,
#     context: Optional[str] = None
# ) -> Optional[Dict]:
#     """Analyze transcript for scam indicators using Google Gemini API.
    
#     Args:
#         transcript: The audio transcript to analyze
#         context: Optional previous context (30-second rolling window)
#     """
#     if not GEMINI_API_KEY:
#         logger.error("Gemini API key not configured")
#         return get_default_analysis()
    
#     try:
#         # Build the prompt with context
#         system_prompt = (
#             "Analyze for scams. Look for: Gift Cards, Crypto, OTP, Money Transfer, Urgent, Threats. "
#             "Respond: {\"risk_level\": \"low|medium|high\", \"scam_type\": \"string\", \"reasons\": [], \"confidence\": 0.0-1.0}"
#         )
        
#         # Reduce context window to last 2 chunks only (instead of 30 seconds)
#         context_truncated = context.split('\n')[-2:] if context else []
#         context_short = '\n'.join(context_truncated) if context_truncated else "No context"
        
#         message_text = f"Context: {context_short}\n\nAnalyze: {transcript}"
        
#         payload = {
#             "contents": [
#                 {
#                     "role": "user",
#                     "parts": [{"text": system_prompt + "\n\n" + message_text}]
#                 }
#             ],
#             "generationConfig": {
#                 "temperature": 0.1,
#                 "maxOutputTokens": 500
#             }
#         }
        
#         headers = {"Content-Type": "application/json"}
#         url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             response = await client.post(url, json=payload, headers=headers)
        
#         if response.status_code == 200:
#             result = response.json()
#             content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
#             logger.info(f"Raw Gemini response (first 300 chars): {content[:300]}")
            
#             # Extract JSON from response
#             import re
            
#             # Remove markdown code blocks if present
#             content_cleaned = re.sub(r'```(?:json)?\s*', '', content)
#             content_cleaned = re.sub(r'```\s*', '', content_cleaned).strip()
            
#             # Find JSON object with proper brace matching
#             try:
#                 # Find the first opening brace
#                 start = content_cleaned.find('{')
#                 if start != -1:
#                     # Count braces to find matching closing brace
#                     brace_count = 0
#                     end = start
#                     for i in range(start, len(content_cleaned)):
#                         if content_cleaned[i] == '{':
#                             brace_count += 1
#                         elif content_cleaned[i] == '}':
#                             brace_count -= 1
#                             if brace_count == 0:
#                                 end = i + 1
#                                 break
                    
#                     if end > start:
#                         json_str = content_cleaned[start:end]
#                         analysis = json.loads(json_str)
#                         # Validation/normalization
#                         analysis["risk_level"] = analysis.get("risk_level", "low").lower()
#                         analysis["scam_type"] = analysis.get("scam_type", None)
#                         analysis["reasons"] = analysis.get("reasons", [])
#                         analysis["confidence"] = float(analysis.get("confidence", 0.0))
#                         logger.info(f"✅ Analysis successful: {analysis['risk_level']}")
#                         return analysis
#                     else:
#                         logger.warning(f"Could not find complete JSON object in: {content_cleaned[:300]}")
#                 else:
#                     logger.warning(f"No opening brace found in: {content_cleaned[:300]}")
#             except json.JSONDecodeError as e:
#                 logger.warning(f"JSON parse error: {str(e)} | Content: {content_cleaned[:300]}")
#             except Exception as e:
#                 logger.error(f"Unexpected error parsing JSON: {str(e)}")
#         else:
#             logger.error(f"Gemini API Error {response.status_code}: {response.text}")
            
#     except Exception as e:
#         logger.error(f"Analysis error: {str(e)}")
    
#     return get_default_analysis()


# def get_default_analysis() -> Dict:
#     return {
#         "risk_level": "low",
#         "scam_type": None,
#         "reasons": ["AI analysis temporarily unavailable (quota exceeded or API error)"],
#         "confidence": 0.0
#     }


"""LLM Analysis service using Google Gemini API.
Analyzes transcripts for scam indicators.

TODO: Integrate Backboard.io for conversation persistence later
"""
import httpx
import json
import logging
from typing import Dict, Optional
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Google Gemini API
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

async def analyze_transcript(
    transcript: str,
    context: Optional[str] = None
) -> Optional[Dict]:
    """Analyze transcript for scam indicators using Google Gemini API.
    
    Args:
        transcript: The audio transcript to analyze
        context: Optional previous context (30-second rolling window)
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API key not configured")
        return get_default_analysis()
    
    try:
        # Build the prompt with context
        system_prompt = (
            "Analyze for scams. Look for: Gift Cards, Crypto, OTP, Money Transfer, Urgent, Threats. "
            "Respond: {\"risk_level\": \"low|medium|high\", \"scam_type\": \"string\", \"reasons\": [], \"confidence\": 0.0-1.0}"
        )
        
        # Reduce context window to last 2 chunks only (instead of 30 seconds)
        context_truncated = context.split('\n')[-2:] if context else []
        context_short = '\n'.join(context_truncated) if context_truncated else "No context"
        
        message_text = f"Context: {context_short}\n\nAnalyze: {transcript}"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": system_prompt + "\n\n" + message_text}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048
            }
        }
        
        headers = {"Content-Type": "application/json"}
        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            logger.info(f"Raw Gemini response (first 300 chars): {content[:300]}")
            
            # Extract JSON from response
            import re
            
            # Remove markdown code blocks if present
            content_cleaned = re.sub(r'```(?:json)?\s*', '', content)
            content_cleaned = re.sub(r'```\s*', '', content_cleaned).strip()
            
            # Find JSON object with proper brace matching
            try:
                # Find the first opening brace
                start = content_cleaned.find('{')
                if start != -1:
                    # Count braces to find matching closing brace
                    brace_count = 0
                    end = start
                    for i in range(start, len(content_cleaned)):
                        if content_cleaned[i] == '{':
                            brace_count += 1
                        elif content_cleaned[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i + 1
                                break
                    
                    if end > start:
                        json_str = content_cleaned[start:end]
                        analysis = json.loads(json_str)
                        # Validation/normalization
                        analysis["risk_level"] = analysis.get("risk_level", "low").lower()
                        analysis["scam_type"] = analysis.get("scam_type", None)
                        analysis["reasons"] = analysis.get("reasons", [])
                        analysis["confidence"] = float(analysis.get("confidence", 0.0))
                        logger.info(f"✅ Analysis successful: {analysis['risk_level']}")
                        return analysis
                    else:
                        logger.warning(f"Could not find complete JSON object in: {content_cleaned[:300]}")
                else:
                    logger.warning(f"No opening brace found in: {content_cleaned[:300]}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {str(e)} | Content: {content_cleaned[:300]}")
            except Exception as e:
                logger.error(f"Unexpected error parsing JSON: {str(e)}")
        else:
            logger.error(f"Gemini API Error {response.status_code}: {response.text}")
            
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
    
    return get_default_analysis()


def get_default_analysis() -> Dict:
    return {
        "risk_level": "low",
        "scam_type": None,
        "reasons": ["AI analysis temporarily unavailable (quota exceeded or API error)"],
        "confidence": 0.0
    }