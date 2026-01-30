import json
import logging
from django.conf import settings
from typing import Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiAI:
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.model = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        return self._client

    def _generate(self, contents, max_tokens: int = 1024) -> Optional[str]:
        if not self.client:
            logger.warning("Gemini client not available")
            return None

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    def generate_from_event_context(
        self,
        title: str,
        short_description: str = "",
        event_type: str = "general",
        location: str = "",
        cover_image_data: bytes = None,
        cover_image_mime: str = "image/jpeg"
    ) -> Optional[dict]:
        prompt = f"""You are a creative event copywriter with a fun, energetic style. Generate content for an event that gets people excited.

Event Title: {title}
Event Type: {event_type}
{f'Current Tagline: {short_description}' if short_description else ''}
{f'Location: {location}' if location else ''}

Generate TWO things:

1. TAGLINE: A catchy, memorable one-liner (max 300 characters) that:
   - Captures the essence of the event
   - Creates curiosity or excitement
   - Is punchy and shareable

2. DESCRIPTION: A fun, engaging description (150-250 words) that:
   - Opens with a hook that grabs attention
   - Has a conversational, upbeat tone
   - Makes readers feel like they'll miss out if they don't attend
   - Highlights the vibe and experience, not just facts
   - Ends with an exciting call to action

IMPORTANT RULES:
- NO emojis whatsoever
- Keep it professional but fun
- Use vivid, descriptive language instead of emojis
- Sound human and enthusiastic, not corporate

{'Analyze the cover image to understand the event theme and atmosphere, and incorporate relevant visual elements into both the tagline and description.' if cover_image_data else ''}

Return as JSON: {{"tagline": "your tagline here", "description": "your description here"}}"""

        contents = []

        if cover_image_data:
            contents.append(
                types.Part.from_bytes(data=cover_image_data, mime_type=cover_image_mime)
            )

        contents.append(prompt)

        result = self._generate(contents, max_tokens=2048)
        if result:
            try:
                clean = result.strip().replace('```json', '').replace('```', '').strip()
                return json.loads(clean)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI response as JSON: {result[:200]}...")
                return {"description": result, "tagline": ""}
        return None

    def generate_event_description(self, title: str, bullet_points: str, event_type: str = "general") -> Optional[str]:
        prompt = f"""You are a creative event copywriter with a fun, energetic style. Generate an event description that gets people pumped.

Event Title: {title}
Event Type: {event_type}
Key Points:
{bullet_points}

Write a fun, engaging description (150-250 words) that:
- Opens with a hook that grabs attention
- Has a conversational, upbeat tone
- Makes readers feel like they'll miss out if they don't attend
- Highlights the vibe and experience
- Ends with an exciting call to action

IMPORTANT RULES:
- NO emojis whatsoever
- Keep it professional but fun
- Use vivid, descriptive language instead of emojis
- Sound human and enthusiastic, not corporate

Return ONLY the description text, no headers or labels."""

        return self._generate(prompt)

    def improve_description(self, description: str) -> Optional[str]:
        prompt = f"""Rewrite this event description to be more fun and engaging while keeping the core message.

Original:
{description}

Make it better by:
- Adding a catchy, attention-grabbing opening
- Using a conversational, upbeat tone
- Making it sound exciting and unmissable
- Fixing any grammar or spelling issues
- Keeping roughly the same length

IMPORTANT RULES:
- NO emojis whatsoever
- Keep it professional but fun
- Use vivid, descriptive language instead of emojis
- Sound human and enthusiastic, not corporate

Return ONLY the improved description."""

        return self._generate(prompt)

    def generate_seo_meta(self, title: str, description: str) -> Optional[dict]:
        prompt = f"""Generate SEO metadata for this event:

Title: {title}
Description: {description}

Return a JSON object with:
- "meta_description": SEO-optimized description (150-160 chars)
- "keywords": comma-separated keywords (5-8 relevant terms)
- "og_title": Open Graph title (60 chars max)

Return ONLY valid JSON, no markdown."""

        result = self._generate(prompt, max_tokens=500)
        if result:
            try:
                clean = result.strip().replace('```json', '').replace('```', '').strip()
                return json.loads(clean)
            except json.JSONDecodeError:
                return None
        return None

    def generate_social_caption(self, title: str, description: str, platform: str = "general") -> Optional[str]:
        char_limits = {
            "twitter": 280,
            "instagram": 2200,
            "facebook": 500,
            "linkedin": 700,
            "general": 300
        }
        limit = char_limits.get(platform, 300)

        prompt = f"""Write a social media caption for this event ({platform}, max {limit} chars):

Event: {title}
About: {description}

Include:
- Attention-grabbing hook
- Key event highlight
- Relevant emojis (2-3)
- Call to action
- Relevant hashtags (3-5)

Return ONLY the caption text."""

        return self._generate(prompt, max_tokens=300)

    def translate_text(self, text: str, target_language: str) -> Optional[str]:
        prompt = f"""Translate this text to {target_language}. Keep the same tone and formatting.

Text:
{text}

Return ONLY the translated text."""

        return self._generate(prompt)

    def summarize_description(self, description: str, max_words: int = 30) -> Optional[str]:
        prompt = f"""Summarize this event description in {max_words} words or less:

{description}

Return ONLY the summary."""

        return self._generate(prompt, max_tokens=150)

    def suggest_ticket_pricing(self, event_type: str, location: str, description: str) -> Optional[dict]:
        prompt = f"""Suggest ticket pricing for this event in Cameroon (XAF currency):

Type: {event_type}
Location: {location}
Description: {description}

Return a JSON object with:
- "early_bird": suggested early bird price in XAF
- "regular": suggested regular price in XAF
- "vip": suggested VIP price in XAF (if applicable)
- "reasoning": brief explanation of pricing strategy

Consider local market conditions in Cameroon. Return ONLY valid JSON."""

        result = self._generate(prompt, max_tokens=500)
        if result:
            try:
                clean = result.strip().replace('```json', '').replace('```', '').strip()
                return json.loads(clean)
            except json.JSONDecodeError:
                return None
        return None

    def generate_image_alt_text(self, image_data: bytes, mime_type: str = "image/jpeg") -> Optional[str]:
        contents = [
            types.Part.from_bytes(data=image_data, mime_type=mime_type),
            """Generate accessible alt text for this event cover image.

Write concise, descriptive alt text (max 125 chars) that:
- Describes the image content
- Is useful for screen readers
- Avoids "image of" or "picture of"

Return ONLY the alt text."""
        ]

        return self._generate(contents, max_tokens=100)

    def answer_event_question(self, event_info: dict, question: str) -> Optional[str]:
        prompt = f"""You are a helpful assistant for an event ticketing platform.

Event Details:
- Title: {event_info.get('title', 'N/A')}
- Date: {event_info.get('date', 'N/A')}
- Location: {event_info.get('location', 'N/A')}
- Description: {event_info.get('description', 'N/A')}
- Ticket Types: {event_info.get('tickets', 'N/A')}

User Question: {question}

Answer helpfully and concisely. If you don't have the information, say so politely.
Keep response under 150 words."""

        return self._generate(prompt, max_tokens=300)

    def generate_analytics_insight(self, metrics: dict) -> Optional[str]:
        prompt = f"""You are an expert event analytics consultant. Analyze these metrics and provide valuable insights.

METRICS:
{json.dumps(metrics, indent=2)}

Write a helpful analysis (3-4 sentences) that:
1. Highlights the most important metric and what it means
2. Identifies any opportunities or areas needing attention
3. Provides a specific, actionable recommendation

RULES:
- Be specific with actual numbers from the data
- Use a professional but friendly tone
- Focus on insights that help improve event performance
- If metrics show zero activity, suggest ways to boost engagement
- NO emojis

Return ONLY the insight text, no headers or labels."""

        return self._generate(prompt, max_tokens=500)

    def suggest_event_tags(self, title: str, description: str) -> Optional[list]:
        prompt = f"""Suggest relevant tags/categories for this event:

Title: {title}
Description: {description}

Return a JSON array of 5-8 relevant tags. Examples: ["technology", "networking", "workshop"]
Return ONLY the JSON array."""

        result = self._generate(prompt, max_tokens=200)
        if result:
            try:
                clean = result.strip().replace('```json', '').replace('```', '').strip()
                return json.loads(clean)
            except json.JSONDecodeError:
                return None
        return None

    def chat(self, prompt: str, max_tokens: int = 2048) -> Optional[str]:
        return self._generate(prompt, max_tokens=max_tokens)

    def chat_with_audio(self, prompt: str, audio_data: bytes, audio_mime: str = "audio/mp3") -> Optional[str]:
        contents = [
            types.Part.from_bytes(data=audio_data, mime_type=audio_mime),
            prompt
        ]
        return self._generate(contents, max_tokens=2048)

    def chat_with_image(self, prompt: str, image_data: bytes, image_mime: str = "image/jpeg") -> Optional[str]:
        contents = [
            types.Part.from_bytes(data=image_data, mime_type=image_mime),
            prompt
        ]
        return self._generate(contents, max_tokens=2048)

    def analyze_image(self, image_data: bytes, prompt: str, image_mime: str = "image/jpeg") -> Optional[str]:
        contents = [
            types.Part.from_bytes(data=image_data, mime_type=image_mime),
            prompt
        ]
        return self._generate(contents, max_tokens=1024)

    def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> Optional[bytes]:
        if not self.client:
            logger.warning("Gemini client not available")
            return None

        try:
            response = self.client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=prompt,
                config={
                    'number_of_images': 1,
                    'aspect_ratio': aspect_ratio,
                    'safety_filter_level': 'block_some',
                    'person_generation': 'allow_adult'
                }
            )

            if response.generated_images:
                return response.generated_images[0].image.image_bytes
            return None
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None


gemini_ai = GeminiAI()
