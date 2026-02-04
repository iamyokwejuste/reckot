import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from apps.core.services.ai import gemini_ai
from apps.events.models import Event
from apps.orgs.models import Organization

logger = logging.getLogger(__name__)


class ConversationalEventCreator:
    def __init__(self):
        self.conversation_history = []
        self.extracted_data = {}
        self.missing_fields = []

    def start_conversation(self, audio_data: bytes, user_id: int = None) -> Dict:
        prompt = """Extract event info from audio. Return JSON with extracted_fields (title, event_type, date, time, location, description, capacity, is_free, pricing), missing_fields list, transcription, language (en/fr), follow_up_questions [{field, question, question_fr}], suggestions, and confidence score."""

        try:
            result = gemini_ai.chat_with_audio(prompt, audio_data)
            analysis = json.loads(result)

            self.extracted_data = analysis.get("extracted_fields", {})
            self.missing_fields = analysis.get("missing_fields", [])
            self.conversation_history.append(
                {
                    "role": "user",
                    "type": "audio",
                    "content": analysis.get("transcription", ""),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "success": True,
                "extracted_data": self.extracted_data,
                "missing_fields": self.missing_fields,
                "questions": analysis.get("follow_up_questions", []),
                "suggestions": analysis.get("suggestions", {}),
                "confidence": analysis.get("confidence", 0),
                "language": analysis.get("language", "en"),
                "ready_to_create": len(self.missing_fields) == 0,
            }

        except Exception as e:
            logger.error(f"Voice conversation start error: {e}")
            return {
                "success": False,
                "error": str(e),
                "questions": self._get_default_questions(),
            }

    def continue_conversation(self, audio_data: bytes, context: Dict = None) -> Dict:
        prompt = f"""Data: {json.dumps(self.extracted_data)} | Missing: {", ".join(self.missing_fields)} | Update from audio. Return JSON: updated_fields, transcription, still_missing, next_question, ready_to_create, confidence."""

        try:
            result = gemini_ai.chat_with_audio(prompt, audio_data)
            response = json.loads(result)

            self.extracted_data.update(response.get("updated_fields", {}))
            self.missing_fields = response.get("still_missing", [])

            self.conversation_history.append(
                {
                    "role": "user",
                    "type": "audio",
                    "content": response.get("transcription", ""),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "success": True,
                "extracted_data": self.extracted_data,
                "missing_fields": self.missing_fields,
                "next_question": response.get("next_question"),
                "ready_to_create": response.get("ready_to_create", False),
                "confidence": response.get("confidence", 0),
            }

        except Exception as e:
            logger.error(f"Voice conversation continue error: {e}")
            return {"success": False, "error": str(e)}

    def finalize_event(self, organization_id: int, user_id: int) -> Dict:
        prompt = f"""Create full event from data: {json.dumps(self.extracted_data)}. Return JSON with: title, short_description, description (HTML 250+ words), event_type, start_at, end_at, timezone, location, venue_name, city, country, capacity, is_free, is_public, ticket_types (name/price/quantity/description), marketing (social_posts, email_subject, hashtags), seo (meta_title/description/keywords), ai_metadata."""

        try:
            result = gemini_ai.chat(prompt)
            event_data = json.loads(result)

            event_data["organization_id"] = organization_id
            event_data["created_by_voice"] = True
            event_data["voice_conversation_id"] = datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )

            return {"success": True, "event_data": event_data, "ready_for_db": True}

        except Exception as e:
            logger.error(f"Event finalization error: {e}")
            return {"success": False, "error": str(e)}

    def create_event_in_db(
        self, event_data: Dict, organization_id: int
    ) -> Optional[Event]:
        try:
            org = Organization.objects.get(id=organization_id)

            event = Event.objects.create(
                organization=org,
                title=event_data.get("title"),
                slug=None,
                short_description=event_data.get("short_description"),
                description=event_data.get("description"),
                event_type=event_data.get("event_type", "IN_PERSON"),
                start_at=datetime.fromisoformat(event_data.get("start_at")),
                end_at=datetime.fromisoformat(event_data.get("end_at")),
                timezone=event_data.get("timezone", "Africa/Douala"),
                location=event_data.get("location"),
                venue_name=event_data.get("venue_name"),
                city=event_data.get("city"),
                country=event_data.get("country", "Cameroon"),
                capacity=event_data.get("capacity", 0),
                is_free=event_data.get("is_free", False),
                is_public=event_data.get("is_public", True),
                state="DRAFT",
            )

            from apps.tickets.models import TicketType

            for ticket in event_data.get("ticket_types", []):
                TicketType.objects.create(
                    event=event,
                    name=ticket.get("name"),
                    price=ticket.get("price", 0),
                    quantity=ticket.get("quantity", 0),
                    description=ticket.get("description", ""),
                    is_active=True,
                )

            logger.info(f"Event created via voice: {event.id}")
            return event

        except Exception as e:
            logger.error(f"DB creation error: {e}")
            return None

    def _get_default_questions(self) -> List[Dict]:
        return [
            {
                "field": "title",
                "question": "What is your event called?",
                "question_fr": "Comment s'appelle votre événement ?",
            },
            {
                "field": "event_type",
                "question": "What type of event is it? (concert, workshop, conference, party, etc.)",
                "question_fr": "Quel type d'événement est-ce ?",
            },
            {
                "field": "date",
                "question": "When will it take place?",
                "question_fr": "Quand aura-t-il lieu ?",
            },
            {
                "field": "location",
                "question": "Where will it be held?",
                "question_fr": "Où se tiendra-t-il ?",
            },
        ]


def generate_cover_from_voice_event(
    event_data: Dict, aspect_ratio: str = "16:9"
) -> Optional[bytes]:
    from PIL import Image
    import io

    title = event_data.get("title", "")
    description = event_data.get("description", "")
    event_type = event_data.get("event_type", "general")

    dimensions = {
        "16:9": (1920, 1080),
        "1:1": (1080, 1080),
        "4:3": (1600, 1200),
        "3:2": (1800, 1200),
        "40x65cm": (2400, 3900),
    }

    target_width, target_height = dimensions.get(aspect_ratio, (1920, 1080))
    aspect_desc = f"{target_width}x{target_height}" if aspect_ratio == "40x65cm" else aspect_ratio

    prompt = f"""{event_type} event image: {title}. {description[:120]}. Aspect ratio {aspect_desc}, {target_width}x{target_height}px exactly. Photorealistic African venue, vibrant modern aesthetic, professional photography quality. NO TEXT overlays."""

    try:
        image_bytes = gemini_ai.generate_image(prompt)

        if image_bytes:
            img = Image.open(io.BytesIO(image_bytes))
            current_width, current_height = img.size

            target_aspect = target_width / target_height
            current_aspect = current_width / current_height

            if abs(current_aspect - target_aspect) > 0.01:
                if current_aspect > target_aspect:
                    new_width = int(current_height * target_aspect)
                    left = (current_width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, current_height))
                else:
                    new_height = int(current_width / target_aspect)
                    top = (current_height - new_height) // 2
                    img = img.crop((0, top, current_width, top + new_height))

            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            img.save(output, format="PNG", quality=95, optimize=True)
            return output.getvalue()

        return None

    except Exception as e:
        logger.error(f"Cover generation error: {e}")
        return None
