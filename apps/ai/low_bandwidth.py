import logging
from typing import Optional
from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)


class LowBandwidthAIService:
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.lite_model = getattr(settings, "GEMINI_LITE_MODEL", "gemini-1.5-flash-8b")
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        return self._client

    def generate_compressed(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.5
    ) -> Optional[str]:
        if not self.client:
            return None

        try:
            response = self.client.models.generate_content(
                model=self.lite_model,
                contents=prompt,
                config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Low-bandwidth generation error: {e}")
            return None

    def summarize_for_mobile(self, text: str, max_words: int = 50) -> Optional[str]:
        prompt = f"""Summarize in {max_words} words or less. Be concise and direct.

Text:
{text[:1000]}

Summary:"""

        return self.generate_compressed(prompt, max_tokens=200)

    def quick_event_description(
        self,
        title: str,
        category: str,
        location: str
    ) -> Optional[str]:
        prompt = f"""Generate a brief event description (30-50 words).

Title: {title}
Category: {category}
Location: {location}

Description:"""

        return self.generate_compressed(prompt, max_tokens=150)

    def mobile_friendly_response(self, query: str, context: str = "") -> Optional[str]:
        prompt = f"""Answer in 2-3 short sentences. Be direct and helpful.

{f"Context: {context[:200]}" if context else ""}

Question: {query}

Answer:"""

        return self.generate_compressed(prompt, max_tokens=200)


low_bandwidth_service = LowBandwidthAIService()
