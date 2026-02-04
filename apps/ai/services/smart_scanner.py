import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from django.conf import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class SmartEventScanner:
    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-3-flash-preview")
        self._client = None
        self.system_prompt = self._load_prompt()

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        return self._client

    def _load_prompt(self) -> str:
        prompt_path = (
            Path(settings.BASE_DIR) / "static" / "markdown" / "smart_scanner.md"
        )
        return prompt_path.read_text(encoding="utf-8")

    def scan_event_image(
        self, image_data: bytes, image_mime: str = "image/jpeg"
    ) -> Optional[Dict[str, Any]]:
        if not self.client:
            logger.warning("Gemini client not available")
            return None

        contents = [
            types.Part.from_bytes(data=image_data, mime_type=image_mime),
            self.system_prompt,
        ]

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config={"max_output_tokens": 2048, "temperature": 0.3},
            )

            result = response.text
            clean = result.strip().replace("```json", "").replace("```", "").strip()

            if "{" in clean and "}" in clean:
                start = clean.find("{")
                end = clean.rfind("}") + 1
                return json.loads(clean[start:end])

            return None

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Smart scanner error: {e}")
            return None

    def scan_competitor_event(
        self,
        image_data: bytes,
        image_mime: str = "image/jpeg",
        your_event_data: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        base_scan = self.scan_event_image(image_data, image_mime)

        if not base_scan or not your_event_data:
            return base_scan

        if not self.client:
            return base_scan

        comparison_prompt = f"""Analyze this competitor event and compare with our event.

COMPETITOR EVENT:
{json.dumps(base_scan, indent=2)}

OUR EVENT:
Title: {your_event_data.get("title")}
Date: {your_event_data.get("date")}
Location: {your_event_data.get("location")}
Prices: {your_event_data.get("prices")}
Category: {your_event_data.get("category")}

Provide competitive analysis with:
1. Pricing strategy comparison
2. Marketing approach differences
3. Target audience insights
4. Competitive advantages we have
5. Recommended counter-strategies

Return JSON:
{{
  "competitor_scan": {{extracted data}},
  "competitive_analysis": {{
    "pricing_comparison": "string",
    "marketing_insights": "string",
    "our_advantages": ["array"],
    "threats": ["array"],
    "recommended_actions": ["array"]
  }}
}}
"""

        try:
            contents = [
                types.Part.from_bytes(data=image_data, mime_type=image_mime),
                comparison_prompt,
            ]

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config={"max_output_tokens": 2048, "temperature": 0.7},
            )

            result = response.text
            clean = result.strip().replace("```json", "").replace("```", "").strip()

            if "{" in clean and "}" in clean:
                start = clean.find("{")
                end = clean.rfind("}") + 1
                return json.loads(clean[start:end])

            return {"competitor_scan": base_scan}

        except Exception as e:
            logger.error(f"Competitive analysis error: {e}")
            return {"competitor_scan": base_scan}

    def validate_event_poster(
        self, image_data: bytes, image_mime: str = "image/jpeg"
    ) -> Dict[str, Any]:
        scan_result = self.scan_event_image(image_data, image_mime)

        if not scan_result:
            return {
                "valid": False,
                "score": 0,
                "issues": ["Unable to scan image"],
                "recommendations": ["Please provide a clearer image"],
            }

        issues = []
        score = 100

        if not scan_result.get("title"):
            issues.append("Missing event title")
            score -= 20

        if not scan_result.get("date"):
            issues.append("Missing event date")
            score -= 15

        if not scan_result.get("location"):
            issues.append("Missing location/venue")
            score -= 15

        if not scan_result.get("prices"):
            issues.append("Missing ticket prices")
            score -= 10

        if scan_result.get("missing_info"):
            for missing in scan_result["missing_info"]:
                if missing not in [i.lower() for i in issues]:
                    issues.append(f"Missing {missing}")
                    score -= 5

        confidence = scan_result.get("confidence_score", 50)
        if confidence < 70:
            score -= (70 - confidence) * 0.5

        recommendations = []
        if issues:
            recommendations.append("Add missing information to improve discoverability")
        if confidence < 80:
            recommendations.append("Use higher resolution image with clearer text")
        if not scan_result.get("social_handles"):
            recommendations.append("Add social media handles for promotion")

        return {
            "valid": score >= 60,
            "score": max(0, int(score)),
            "scan_data": scan_result,
            "issues": issues,
            "recommendations": recommendations,
        }


smart_scanner = SmartEventScanner()
