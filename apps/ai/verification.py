from typing import Dict, Optional
from decimal import Decimal
from apps.core.services.ai import gemini_ai


def verify_event_authenticity(
    title: str,
    description: str,
    price: Decimal,
    capacity: int,
    location: str,
    organizer_history: Optional[Dict] = None,
    cover_image_data: Optional[bytes] = None
) -> Dict:
    organizer_context = ""
    if organizer_history:
        organizer_context = f"""
        Organizer History:
        - Total events: {organizer_history.get('total_events', 0)}
        - Successful events: {organizer_history.get('successful_events', 0)}
        - Average rating: {organizer_history.get('avg_rating', 0)}/5
        - Refund rate: {organizer_history.get('refund_rate', 0)}%
        """

    prompt = f"""You are an event fraud detection expert for African markets. Analyze this event for authenticity and potential scam indicators.

Event Details:
Title: {title}
Description: {description}
Price: {price} XAF
Capacity: {capacity}
Location: {location}
{organizer_context}

Analysis Criteria:
1. Price Realism: Is the price reasonable for this type of event in Africa?
2. Capacity Claims: Is the capacity realistic for the stated location?
3. Description Quality: Does it contain typical scam language? (e.g., "guaranteed", "limited time", excessive urgency)
4. Location Verification: Is it a real, verifiable location?
5. Organizer Trust: Based on history, is this organizer reliable?
6. Common Scams: Check for pyramid schemes, fake concerts, non-existent venues

Provide analysis in this exact JSON format:
{{
    "trust_score": <0-100>,
    "risk_level": "<LOW|MEDIUM|HIGH>",
    "flags": ["list", "of", "concerns"],
    "recommendations": ["list", "of", "suggestions"],
    "reasoning": "brief explanation",
    "verified": <true|false>
}}

Focus on African market context - events here often use mobile money, smaller venues, and different pricing structures."""

    result = gemini_ai.chat(prompt)

    try:
        import json
        analysis = json.loads(result)

        if cover_image_data:
            image_analysis = _analyze_event_image(cover_image_data, title, description)
            analysis['image_analysis'] = image_analysis

            if image_analysis.get('suspicious', False):
                analysis['trust_score'] = max(0, analysis['trust_score'] - 20)
                analysis['flags'].extend(image_analysis.get('concerns', []))

        if analysis['trust_score'] < 40:
            analysis['risk_level'] = 'HIGH'
        elif analysis['trust_score'] < 70:
            analysis['risk_level'] = 'MEDIUM'
        else:
            analysis['risk_level'] = 'LOW'

        return analysis

    except json.JSONDecodeError:
        return {
            'trust_score': 50,
            'risk_level': 'MEDIUM',
            'flags': ['Unable to complete full analysis'],
            'recommendations': ['Manual review recommended'],
            'verified': False,
            'error': 'Analysis parsing failed'
        }


def _analyze_event_image(image_data: bytes, title: str, description: str) -> Dict:
    prompt = f"""Analyze this event poster/cover image for authenticity.

Event Title: {title}
Event Description: {description[:200]}...

Check for:
1. Is this a generic stock photo?
2. Does the image match the event description?
3. Are there signs of poor quality/rushed design?
4. Any suspicious elements (fake celebrity endorsements, etc)?
5. Professional vs amateur design quality

Return JSON:
{{
    "suspicious": <true|false>,
    "quality_score": <0-100>,
    "concerns": ["list of issues"],
    "analysis": "brief description"
}}"""

    try:
        result = gemini_ai.chat_with_image(prompt, image_data)
        import json
        return json.loads(result)
    except Exception:
        return {'suspicious': False, 'quality_score': 50, 'concerns': [], 'analysis': 'Image analysis unavailable'}


def get_fraud_prevention_tips() -> list[str]:
    return [
        "Verify organizer identity through social media profiles",
        "Check if venue is a real, bookable location",
        "Be cautious of prices significantly below market rate",
        "Look for organizer's previous event history",
        "Avoid events demanding urgent payment or 'limited slots'",
        "Verify celebrity/VIP appearances through official channels",
        "Use Reckot's trusted organizers for added security"
    ]
