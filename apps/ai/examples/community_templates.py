import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)


class CommunityEventTemplates:
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-3-flash-preview")
        self._client = None
        self.system_prompt = self._load_prompt()

        self.event_types = {
            'church': 'Church Gatherings',
            'village': 'Village Ceremonies',
            'street_festival': 'Street Festivals',
            'university': 'University Events',
            'market': 'Market Days',
            'youth': 'Youth Programs'
        }

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        return self._client

    def _load_prompt(self) -> str:
        prompt_path = Path(settings.BASE_DIR) / 'static' / 'markdown' / 'community_templates.md'
        return prompt_path.read_text(encoding='utf-8')

    def generate_community_event(
        self,
        event_type: str,
        title: str,
        location: str,
        date: str,
        additional_details: str = ""
    ) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None

        event_category = self.event_types.get(event_type, 'Church Gatherings')

        prompt = f"""{self.system_prompt}

Generate content for a {event_category} event:

Title: {title}
Location: {location}
Date: {date}
{f"Additional Details: {additional_details}" if additional_details else ""}

Provide culturally relevant content in JSON format:
{{
  "description": "engaging description (150-200 words)",
  "tagline": "catchy tagline (max 100 chars)",
  "suggested_pricing": {{
    "free": boolean,
    "early_bird": "amount in XAF or null",
    "regular": "amount in XAF or null",
    "vip": "amount in XAF or null"
  }},
  "target_audience": "description",
  "marketing_tips": ["array of 3-5 tips"],
  "cultural_considerations": ["array of 2-3 points"],
  "promotion_channels": ["WhatsApp", "Facebook", etc],
  "language_suggestion": "English/French/Both"
}}"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"max_output_tokens": 2048, "temperature": 0.7}
            )

            result = response.text
            clean = result.strip().replace("```json", "").replace("```", "").strip()

            if "{" in clean and "}" in clean:
                start = clean.find("{")
                end = clean.rfind("}") + 1
                return json.loads(clean[start:end])

            return None

        except Exception as e:
            logger.error(f"Community template generation error: {e}")
            return None

    def get_template_suggestions(self, event_type: str) -> Dict[str, Any]:
        event_category = self.event_types.get(event_type)

        if not event_category:
            return {
                "error": "Unknown event type",
                "available_types": list(self.event_types.keys())
            }

        templates = {
            'church': {
                'typical_attendance': '50-500',
                'pricing_range': 'Free or donations',
                'best_days': 'Sundays, Wednesdays',
                'duration': '2-4 hours',
                'venue_types': ['Church building', 'Community hall', 'Open field']
            },
            'village': {
                'typical_attendance': '100-1000',
                'pricing_range': 'Free or contribution',
                'best_days': 'Weekends, public holidays',
                'duration': '4-8 hours',
                'venue_types': ['Village square', 'Chief\'s compound', 'Community center']
            },
            'street_festival': {
                'typical_attendance': '500-5000',
                'pricing_range': '1,000-5,000 XAF',
                'best_days': 'Saturdays, public holidays',
                'duration': '6-12 hours',
                'venue_types': ['Main street', 'Public square', 'Market area']
            },
            'university': {
                'typical_attendance': '100-2000',
                'pricing_range': '500-3,000 XAF',
                'best_days': 'Weekdays, Friday nights',
                'duration': '2-6 hours',
                'venue_types': ['Campus hall', 'Auditorium', 'Sports field']
            },
            'market': {
                'typical_attendance': '200-2000',
                'pricing_range': 'Free entry, vendor fees',
                'best_days': 'Market days, weekends',
                'duration': '6-10 hours',
                'venue_types': ['Market square', 'Exhibition center', 'Open lot']
            },
            'youth': {
                'typical_attendance': '50-500',
                'pricing_range': 'Free or 500-2,000 XAF',
                'best_days': 'Saturdays, school holidays',
                'duration': '3-6 hours',
                'venue_types': ['Youth center', 'Sports ground', 'School compound']
            }
        }

        return {
            'event_type': event_type,
            'category': event_category,
            'template_data': templates.get(event_type, {}),
            'cultural_context': f"Generated for Cameroon {event_category.lower()}"
        }


community_templates = CommunityEventTemplates()
