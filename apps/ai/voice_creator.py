from typing import Dict, Optional
from datetime import datetime
from apps.core.services.ai import gemini_ai


def create_event_from_voice(audio_data: bytes, user_language: str = "auto") -> Dict:
    prompt = """You are an expert event planner for Africa. A user has described an event in their own words (possibly in French or English). Extract structured event information.

Your task:
1. Transcribe the audio to text
2. Identify the language (French or English)
3. Extract ALL event details mentioned
4. Infer missing details intelligently
5. Suggest appropriate pricing for African market

Extract these fields:
- Event title (catchy, professional)
- Short tagline (one sentence, compelling hook)
- Full description (professional, engaging)
- Event type (conference, concert, workshop, party, sports, etc.)
- Date and time (if mentioned, else suggest)
- Location/venue (exact address if mentioned)
- Expected capacity (infer from context)
- Suggested pricing in XAF (based on event type)
- Ticket types (VIP, Regular, Early Bird, etc.)

Return ONLY valid JSON:
{
    "title": "Professional event title",
    "tagline": "One compelling sentence about the event",
    "description": "Detailed, engaging description (200+ words)",
    "event_type": "category",
    "date": "2026-02-15",
    "time": "18:00",
    "location": "specific venue and address",
    "capacity": 100,
    "suggested_price": 5000,
    "ticket_types": [
        {"name": "Regular", "price": 5000, "quantity": 80},
        {"name": "VIP", "price": 10000, "quantity": 20}
    ],
    "confidence": 0.95,
    "original_text": "transcribed audio",
    "language_detected": "fr",
    "missing_fields": ["list", "of", "fields", "we", "inferred"],
    "suggestions": ["helpful tips for organizer"]
}

Context for pricing (Cameroon/Africa):
- Small workshop: 1,000-5,000 XAF
- Concert/party: 2,000-15,000 XAF
- Conference: 5,000-25,000 XAF
- VIP tickets: 2-3x regular price
- Free events: community/educational"""

    try:
        result = gemini_ai.chat_with_audio(prompt, audio_data)
        import json

        event_data = json.loads(result)

        if event_data.get("confidence", 0) < 0.6:
            event_data["warnings"] = [
                "Low confidence in extraction",
                "Please review and confirm all details",
            ]

        event_data["created_at"] = datetime.now().isoformat()
        event_data["ai_generated"] = True

        return event_data

    except json.JSONDecodeError:
        return {
            "error": "Unable to parse voice input",
            "suggestion": "Please try again with clearer audio",
            "confidence": 0,
        }


def enhance_voice_created_event(
    event_data: Dict, cover_image_data: Optional[bytes] = None
) -> Dict:
    prompt = f"""Enhance this AI-generated event with professional marketing content.

Original Event:
Title: {event_data.get("title")}
Description: {event_data.get("description")}
Type: {event_data.get("event_type")}
Location: {event_data.get("location")}

Create:
1. Improved description (250-300 words, engaging, professional)
2. SEO-friendly title and meta description
3. 3 social media post variations (WhatsApp, Facebook, Twitter style)
4. Email invitation subject + preview
5. Marketing tips specific to this event type in Africa

Return JSON:
{{
    "enhanced_description": "...",
    "seo_title": "...",
    "seo_description": "...",
    "social_posts": {{
        "whatsapp": "...",
        "facebook": "...",
        "twitter": "..."
    }},
    "email_subject": "...",
    "email_preview": "...",
    "marketing_tips": ["tip1", "tip2", "tip3"]
}}"""

    result = gemini_ai.chat(prompt)

    try:
        import json

        enhancements = json.loads(result)

        if cover_image_data:
            image_context = gemini_ai.analyze_image(
                cover_image_data,
                "Describe this event image. What vibe, theme, and audience does it suggest?",
            )
            enhancements["image_context"] = image_context

        return {**event_data, **enhancements, "fully_enhanced": True}

    except json.JSONDecodeError:
        return event_data


def voice_feedback_loop(event_data: Dict, user_voice_feedback: bytes) -> Dict:
    prompt = f"""A user created an event via voice and now wants to modify it.

Current Event:
{event_data}

User's voice feedback: [AUDIO TRANSCRIBED]

Task:
1. Understand what they want to change
2. Update the appropriate fields
3. Maintain consistency across all fields

Return the complete updated event JSON with changes marked."""

    result = gemini_ai.chat_with_audio(prompt, user_voice_feedback)

    try:
        import json

        updated_event = json.loads(result)
        updated_event["revision_count"] = event_data.get("revision_count", 0) + 1
        updated_event["last_modified_via"] = "voice"

        return updated_event

    except json.JSONDecodeError:
        return event_data


def transcribe_audio(audio_data: bytes, language: str = "auto") -> str | None:
    prompt = f"""Transcribe this audio accurately. Language: {language}

Return only the transcribed text, nothing else."""

    return gemini_ai.chat_with_audio(prompt, audio_data)
