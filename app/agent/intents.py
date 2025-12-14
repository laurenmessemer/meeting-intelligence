"""Intent recognition - classify user intent using LLM."""
import json
from typing import Dict, Any
from app.llm.client import chat
from app.llm.prompts import INTENT_RECOGNITION_SYSTEM, INTENT_RECOGNITION_USER


def recognize_intent(user_message: str) -> Dict[str, Any]:
    """
    Classify user intent and extract entities.
    
    Returns:
        {
            "intent": "summarize_meeting" | "other",
            "confidence": 0.0-1.0,
            "entities": {
                "client_name": str | None,
                "date": str | None
            }
        }
    """
    prompt = INTENT_RECOGNITION_USER.format(user_message=user_message)
    
    response_text = chat(
        prompt=prompt,
        system_prompt=INTENT_RECOGNITION_SYSTEM,
        temperature=0.3,  # Lower temperature for classification
        response_format={"response_mime_type": "application/json"}
    )
    
    try:
        result = json.loads(response_text)
        return {
            "intent": result.get("intent", "other"),
            "confidence": float(result.get("confidence", 0.0)),
            "entities": result.get("entities", {})
        }
    except (json.JSONDecodeError, ValueError, KeyError):
        # Fallback to default
        return {
            "intent": "other",
            "confidence": 0.0,
            "entities": {}
        }
