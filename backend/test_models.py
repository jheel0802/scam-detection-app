import httpx
import json
import asyncio
from config import BACKBOARD_API_KEY

BACKBOARD_BASE_URL = "https://app.backboard.io/api"
BACKBOARD_HEADERS = {"X-API-Key": BACKBOARD_API_KEY}

async def test_backboard():
    print("Testing Backboard API...\n")
    
    # Test 1: Create Assistant
    print("1️⃣ Creating Scam Detection Assistant...")
    assistant_payload = {
        "name": "Scam Call Detector",
        "system_prompt": "You are a fraud detection expert. Respond in JSON format with: {\"risk_level\": \"low|medium|high\", \"scam_type\": \"string\", \"reasons\": [\"list\"], \"confidence\": 0.0-1.0}"
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        assistant_response = await client.post(
            f"{BACKBOARD_BASE_URL}/assistants",
            json=assistant_payload,
            headers=BACKBOARD_HEADERS
        )
    
    print(f"Status: {assistant_response.status_code}")
    print(f"Response: {assistant_response.text}\n")
    
    if assistant_response.status_code not in [200, 201]:
        print("❌ Failed to create assistant")
        return
    
    result = assistant_response.json()
    assistant_id = result.get("assistant_id") or result.get("id")
    print(f"✅ Assistant created: {assistant_id}\n")
    
    # Test 2: Try different conversation endpoints
    print("2️⃣ Creating Conversation Thread...")
    
    # Try different endpoint formats
    endpoints_to_try = [
        f"{BACKBOARD_BASE_URL}/conversations",
        f"{BACKBOARD_BASE_URL}/assistants/{assistant_id}/conversations",
    ]
    
    conv_payload = {"assistant_id": assistant_id}
    
    for endpoint in endpoints_to_try:
        print(f"  Trying: {endpoint}")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                conv_response = await client.post(
                    endpoint,
                    json=conv_payload,
                    headers=BACKBOARD_HEADERS
                )
            
            print(f"  Status: {conv_response.status_code}")
            
            if conv_response.status_code in [200, 201]:
                print(f"  ✅ Success!")
                conv_result = conv_response.json()
                conversation_id = conv_result.get("conversation_id") or conv_result.get("id") or conv_result.get("thread_id")
                print(f"  Response: {conv_response.text}\n")
                break
            else:
                print(f"  ❌ Failed: {conv_response.text}\n")
                conversation_id = None
        except Exception as e:
            print(f"  Error: {e}\n")
            conversation_id = None
    
    if not conversation_id:
        print("⚠️ Couldn't create conversation. Trying to send message directly...\n")
        conversation_id = "test-conv"  # Fallback
    
    # Test 3: Send Message
    print("3️⃣ Sending message for analysis...")
    message_payload = {
        "role": "user",
        "content": "Analyze this transcript: 'Hello, we detected suspicious activity on your bank account. You need to verify your details immediately using gift cards to confirm your identity.'"
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        message_response = await client.post(
            f"{BACKBOARD_BASE_URL}/conversations/{conversation_id}/messages",
            json=message_payload,
            headers=BACKBOARD_HEADERS
        )
    
    print(f"Status: {message_response.status_code}")
    print(f"Response: {message_response.text}\n")
    
    if message_response.status_code in [200, 201]:
        print("✅ Message sent and analysis received!")
    else:
        print("❌ Failed to send message")

asyncio.run(test_backboard())
