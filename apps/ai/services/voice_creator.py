import json
from typing import Dict, Optional
from datetime import datetime
from apps.core.services.ai import gemini_ai


def create_event_from_voice(audio_data: bytes, user_language: str = "auto") -> Dict:
    prompt = """Extract event from audio. Return JSON: title, tagline, description (200+ words), event_type, date, time, location, capacity, suggested_price, ticket_types, confidence, original_text, language_detected, missing_fields, suggestions."""

    try:
        result = gemini_ai.chat_with_audio(prompt, audio_data)

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
    prompt = f"""Enhance: {event_data.get("title")} ({event_data.get("event_type")}), {event_data.get("location")}. Return JSON: enhanced_description (250-300 words), seo_title, seo_description, social_posts (whatsapp/facebook/twitter), email_subject, email_preview, marketing_tips."""

    result = gemini_ai.chat(prompt)

    try:
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
    prompt = f"""Current: {event_data}. Update from audio feedback. Return complete updated JSON."""

    result = gemini_ai.chat_with_audio(prompt, user_voice_feedback)

    try:
        updated_event = json.loads(result)
        updated_event["revision_count"] = event_data.get("revision_count", 0) + 1
        updated_event["last_modified_via"] = "voice"

        return updated_event

    except json.JSONDecodeError:
        return event_data


def transcribe_audio(audio_data: bytes, language: str = "auto") -> str | None:
    prompt = f"""Transcribe audio ({language}). Text only."""

    return gemini_ai.chat_with_audio(prompt, audio_data)
