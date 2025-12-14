"""LLM client - wraps Gemini API."""
import google.generativeai as genai
from typing import Optional, Dict, Any
from app.config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)


def chat(prompt: str, system_prompt: Optional[str] = None, 
         temperature: float = 0.7, response_format: Optional[Dict[str, Any]] = None) -> str:
    """
    Single method for LLM interaction.
    
    Args:
        prompt: User prompt
        system_prompt: System instructions (prepended to prompt)
        temperature: Sampling temperature
        response_format: Optional format constraints (e.g., JSON schema)
    
    Returns:
        LLM response text
    """
    model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    # Combine system prompt and user prompt
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    
    # Configure generation settings
    generation_config = {
        "temperature": temperature,
    }
    
    if response_format:
        generation_config.update(response_format)
    
    response = model.generate_content(
        full_prompt,
        generation_config=generation_config
    )
    
    return response.text
