from typing import Dict, List
from datetime import datetime, timedelta
from decimal import Decimal
from apps.core.services.ai import gemini_ai


def predict_ticket_sales(
    event_title: str,
    event_type: str,
    price: Decimal,
    capacity: int,
    location: str,
    start_date: datetime,
    organizer_history: Dict,
    market_data: List[Dict] = None
) -> Dict:
    history_context = f"""
    Organizer History:
    - Previous events: {organizer_history.get('total_events', 0)}
    - Average attendance: {organizer_history.get('avg_attendance', 0)}
    - Average price point: {organizer_history.get('avg_price', 0)} XAF
    - Typical sell-through: {organizer_history.get('avg_sell_through', 0)}%
    """

    market_context = ""
    if market_data:
        market_context = "Similar Events Data:\n"
        for event in market_data[:5]:
            market_context += f"- {event['type']}: {event['sold']}/{event['capacity']} @ {event['price']} XAF\n"

    days_until_event = (start_date - datetime.now()).days

    prompt = f"""You are a data scientist specializing in African event markets. Predict ticket sales for this event.

Event Details:
Title: {event_title}
Type: {event_type}
Price: {price} XAF
Capacity: {capacity}
Location: {location}
Days until event: {days_until_event}

{history_context}
{market_context}

Factors to consider:
1. Price elasticity in African markets
2. Event type popularity
3. Day of week / time of day
4. Organizer track record
5. Location accessibility
6. Typical sales curves (early vs late buyers)

Provide prediction in JSON:
{{
    "predicted_sales": <number>,
    "predicted_percentage": <0-100>,
    "confidence": <0-1>,
    "sales_curve": [
        {{"days_before_event": 30, "cumulative_sales": 10}},
        {{"days_before_event": 15, "cumulative_sales": 40}},
        {{"days_before_event": 7, "cumulative_sales": 65}},
        {{"days_before_event": 1, "cumulative_sales": 85}}
    ],
    "recommendations": [
        "specific actionable advice"
    ],
    "risk_factors": [
        "potential issues that might reduce sales"
    ],
    "optimal_price": <suggested price in XAF>,
    "pricing_analysis": {{
        "current_price_rating": "LOW|OPTIMAL|HIGH",
        "price_elasticity": "description",
        "suggested_tiers": [
            {{"type": "Early Bird", "price": 3000, "quantity": 50}},
            {{"type": "Regular", "price": 5000, "quantity": 80}},
            {{"type": "VIP", "price": 10000, "quantity": 20}}
        ]
    }},
    "best_launch_time": "optimal day/time to launch ticket sales",
    "marketing_strategy": [
        "channel-specific recommendations"
    ]
}}

Base predictions on African market realities:
- Mobile money payment behavior
- Last-minute buying patterns common
- WhatsApp marketing effectiveness
- Price sensitivity varies by region
"""

    result = gemini_ai.chat(prompt)

    try:
        import json
        prediction = json.loads(result)
        prediction['generated_at'] = datetime.now().isoformat()
        prediction['model_version'] = 'gemini-predictive-v1'

        return prediction

    except json.JSONDecodeError:
        return {
            'error': 'Unable to generate prediction',
            'predicted_sales': int(capacity * 0.6),
            'confidence': 0.3
        }


def optimize_ticket_pricing(
    event_data: Dict,
    competitor_events: List[Dict] = None,
    demand_signals: Dict = None
) -> Dict:
    competitor_context = ""
    if competitor_events:
        competitor_context = "Competitor Events:\n"
        for event in competitor_events[:3]:
            competitor_context += f"- {event['title']}: {event['price']} XAF (sold {event.get('sold', 0)}/{event.get('capacity', 0)})\n"

    demand_context = ""
    if demand_signals:
        demand_context = f"""
        Demand Signals:
        - Page views: {demand_signals.get('page_views', 0)}
        - Wishlist adds: {demand_signals.get('wishlist', 0)}
        - Abandoned carts: {demand_signals.get('abandoned_carts', 0)}
        - Social shares: {demand_signals.get('shares', 0)}
        """

    prompt = f"""As a pricing strategist for African events, optimize pricing for this event.

Event: {event_data.get('title')}
Type: {event_data.get('type')}
Current Price: {event_data.get('price')} XAF
Capacity: {event_data.get('capacity')}

{competitor_context}
{demand_context}

Optimize for:
1. Maximum revenue (not just sales)
2. Fairness and accessibility
3. Creating urgency without alienating buyers
4. African market purchasing power

Return JSON:
{{
    "optimal_base_price": <XAF>,
    "revenue_projection": <XAF>,
    "tier_strategy": [
        {{
            "name": "Early Bird",
            "price": <XAF>,
            "allocation": <percentage>,
            "deadline": "2 weeks before event",
            "rationale": "why this tier"
        }}
    ],
    "discount_strategy": {{
        "group_discount": {{"threshold": 5, "discount": 10}},
        "student_discount": 15,
        "early_bird": 25
    }},
    "dynamic_pricing_rules": [
        "if 50% sold and >2 weeks remaining, maintain price",
        "if <30% sold and <1 week remaining, reduce by 15%",
        "if >80% sold, increase remaining tickets by 10%"
    ],
    "upsell_opportunities": [
        "VIP upgrade for +5000 XAF (includes...)",
        "Group packages"
    ],
    "expected_revenue": <total XAF>,
    "confidence": <0-1>
}}"""

    result = gemini_ai.chat(prompt)

    try:
        import json
        return json.loads(result)
    except json.JSONDecodeError:
        return {'error': 'Pricing optimization failed'}


def generate_marketing_strategy(
    event_data: Dict,
    budget: Decimal,
    target_audience: str = None
) -> Dict:
    prompt = f"""Create a detailed marketing strategy for this African event.

Event: {event_data.get('title')}
Type: {event_data.get('type')}
Location: {event_data.get('location')}
Budget: {budget} XAF
Target Audience: {target_audience or 'General'}

Focus on effective African marketing channels:
1. WhatsApp (most important)
2. Facebook
3. Instagram
4. SMS
5. Local radio
6. Community outreach
7. Influencer partnerships (local)

Return actionable strategy in JSON:
{{
    "channel_allocation": {{
        "whatsapp": {{"budget": <XAF>, "strategy": "...", "expected_reach": <number>}},
        "facebook": {{"budget": <XAF>, "strategy": "..."}},
        ...
    }},
    "content_calendar": [
        {{"day": -30, "channel": "whatsapp", "content": "...", "target": "..."}},
        {{"day": -14, "channel": "facebook", "content": "..."}},
        ...
    ],
    "influencer_strategy": {{
        "tier": "micro-influencers",
        "budget": <XAF>,
        "expected_reach": <number>
    }},
    "community_partnerships": ["local organizations to partner with"],
    "early_bird_strategy": "timing and messaging",
    "urgency_tactics": ["ethical scarcity techniques"],
    "expected_roi": <multiplier>,
    "kpis_to_track": ["metric1", "metric2"]
}}"""

    result = gemini_ai.chat(prompt)

    try:
        import json
        return json.loads(result)
    except json.JSONDecodeError:
        return {'error': 'Marketing strategy generation failed'}
