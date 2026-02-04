import json
import logging
import asyncio
from typing import AsyncIterator
from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)


class StreamingGeminiService:
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-3-flash-preview")
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        return self._client

    async def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        if not self.client:
            yield json.dumps({"error": "AI service not configured"})
            return

        try:
            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )

            for chunk in response:
                if chunk.text:
                    yield json.dumps({"chunk": chunk.text, "done": False})
                    await asyncio.sleep(0.01)

            yield json.dumps({"chunk": "", "done": True})

        except Exception as e:
            logger.error(f"Streaming generation error: {e}")
            yield json.dumps({"error": str(e), "done": True})

    async def stream_chat(
        self,
        user_message: str,
        conversation_history: list,
        system_prompt: str = ""
    ) -> AsyncIterator[str]:
        history_str = "\n".join([
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in conversation_history[-10:]
        ])

        full_prompt = f"""{system_prompt}

Conversation History:
{history_str}

User: {user_message}

Respond naturally and helpfully."""

        async for chunk_data in self.stream_generate(full_prompt):
            yield chunk_data


streaming_service = StreamingGeminiService()