"""Intent recognition - classify user intent using LLM."""
import json
import re
from typing import Dict, Any
from app.llm.client import chat
from app.llm.prompts import INTENT_RECOGNITION_SYSTEM, INTENT_RECOGNITION_USER

import re

def _extract_json(text: str) -> Dict[str, Any]:
    """
    Safely extract JSON object from LLM output.
    Handles markdown fences and stray text.
    """
    text = text.strip()

    # Remove markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: extract first JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")

    return json.loads(match.group(0))


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
        temperature=0.0  # force deterministic JSON
    )

    
    try:
        result = _extract_json(response_text)
        print("=" * 80)
        print("DIAGNOSTIC: Intent recognition result")
        print("=" * 80)
        print(f"DIAGNOSTIC: Raw LLM response: {response_text}")
        print(f"DIAGNOSTIC: Parsed result: {result}")
        print(f"DIAGNOSTIC: entities: {result.get('entities', {})}")
        print(f"DIAGNOSTIC: entities['date']: {repr(result.get('entities', {}).get('date'))}")
        return {
            "intent": result.get("intent", "other"),
            "confidence": float(result.get("confidence", 0.0)),
            "entities": result.get("entities", {})
        }
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"DIAGNOSTIC: JSON parsing failed: {type(e).__name__}: {e}")
        print(f"DIAGNOSTIC: Falling back to default (empty entities)")
        # Fallback to default
        return {
            "intent": "other",
            "confidence": 0.0,
            "entities": {}
        }
