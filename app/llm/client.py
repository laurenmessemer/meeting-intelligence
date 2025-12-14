"""LLM client - wraps Gemini API (safe, validated)."""

import google.generativeai as genai
from typing import Optional, Dict, Any
from app.config import Config


class GeminiClient:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise RuntimeError("❌ GEMINI_API_KEY is not set")

        # Explicit API key binding (prevents ADC fallback)
        genai.configure(api_key=Config.GEMINI_API_KEY)

        self.model = self._select_model()

    def _select_model(self):
        """
        Deterministic Gemini model selection.
        Avoids list_models() ambiguity and 404s.
        """

        model_name = (
            f"models/{Config.GEMINI_MODEL}"
            if not Config.GEMINI_MODEL.startswith("models/")
            else Config.GEMINI_MODEL
        )

        try:
            model = genai.GenerativeModel(model_name)

            # Smoke test to ensure the model is callable
            model.generate_content(
                "ping",
                generation_config=genai.types.GenerationConfig(temperature=0),
            )

            print(f"✅ Using Gemini model: {model_name}")
            return model

        except Exception as e:
            raise RuntimeError(
                f"❌ Gemini model '{model_name}' is not callable. "
                f"Check API access or change GEMINI_MODEL. Error: {e}"
            )

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        full_prompt = (
            f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        )

        generation_config = {"temperature": temperature}

        if response_format:
            # Only allow keys supported by older Gemini SDKs
            allowed_keys = {
                "max_output_tokens",
                "top_p",
                "top_k",
                "candidate_count",
                "stop_sequences",
            }

            safe_format = {
                k: v for k, v in response_format.items() if k in allowed_keys
            }

            generation_config.update(safe_format)


        response = self.model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(**generation_config),
        )

        return response.text.strip()


# ---- Public function used by the rest of your app ----

_client: Optional[GeminiClient] = None


def chat(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    response_format: Optional[Dict[str, Any]] = None,
) -> str:
    global _client
    if _client is None:
        _client = GeminiClient()

    return _client.chat(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        response_format=response_format,
    )
