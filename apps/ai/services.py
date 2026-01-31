import json
import logging
from typing import Optional
from google import genai
from django.conf import settings
from django.db.models import Count, Sum, Q, F
from django.utils import timezone

from django.contrib.auth import get_user_model

from apps.events.models import Event
from apps.tickets.models import Ticket, Booking, TicketType
from apps.payments.models import Payment
from apps.orgs.models import Organization

User = get_user_model()

logger = logging.getLogger(__name__)


class GeminiService:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._init_client()
        return cls._instance

    @classmethod
    def _init_client(cls):
        api_key = getattr(settings, "GEMINI_API_KEY", "")
        if api_key:
            cls._client = genai.Client(api_key=api_key)

    @property
    def model(self):
        return getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")

    def is_available(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        if not self.is_available():
            return "AI service is not available. Please configure GEMINI_API_KEY."
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"max_output_tokens": max_tokens, "temperature": 0.7},
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"Error generating response: {str(e)}"

    def generate_json(self, prompt: str, max_tokens: int = 1024) -> dict:
        response = self.generate(prompt, max_tokens)
        try:
            clean = response.strip().replace("```json", "").replace("```", "").strip()
            if "{" in clean and "}" in clean:
                start = clean.find("{")
                end = clean.rfind("}") + 1
                return json.loads(clean[start:end])
        except json.JSONDecodeError:
            pass
        return {"error": "Failed to parse response", "raw": response}


gemini = GeminiService()


def get_model_schema():
    schema = {
        "User": {
            "description": "User accounts (DO NOT expose sensitive data)",
            "fields": {
                "username": "Username",
                "email": "Email address (PRIVATE)",
                "first_name": "First name",
                "last_name": "Last name",
                "is_active": "Is account active",
            },
            "security": "NEVER expose emails or personal data publicly. Only count users.",
        },
        "Event": {
            "description": "Events in the system",
            "fields": {
                "title": "Event title",
                "description": "Event description",
                "location": "Event location",
                "start_at": "Start datetime",
                "end_at": "End datetime",
                "is_public": "Is event public (True) or private (False)",
                "state": "DRAFT, PUBLISHED, or CANCELLED",
                "capacity": "Maximum capacity",
                "organization": "ForeignKey to Organization",
            },
            "filtering": "ALWAYS filter is_public=True when counting public events",
        },
        "Ticket": {
            "description": "Individual tickets",
            "fields": {
                "booking": "ForeignKey to Booking",
                "ticket_type": "ForeignKey to TicketType",
                "status": "VALID, USED, CANCELLED, or REFUNDED",
                "checked_in_at": "Check-in timestamp",
            },
        },
        "Booking": {
            "description": "Ticket bookings",
            "fields": {
                "event": "ForeignKey to Event",
                "user": "ForeignKey to User",
                "status": "PENDING, CONFIRMED, CANCELLED, or REFUNDED",
                "total_amount": "Total payment amount in XAF",
                "created_at": "Booking creation time",
            },
        },
        "Payment": {
            "description": "Payment transactions",
            "fields": {
                "booking": "ForeignKey to Booking",
                "amount": "Payment amount in XAF",
                "status": "PENDING, COMPLETED, FAILED, or REFUNDED",
                "gateway": "Payment gateway used",
                "created_at": "Payment timestamp",
            },
        },
        "Organization": {
            "description": "Event organizations",
            "fields": {
                "name": "Organization name",
                "slug": "URL slug",
                "members": "ManyToMany to User",
            },
        },
    }
    return schema


def execute_django_query(query_code: str):
    try:
        safe_namespace = {
            "User": User,
            "Event": Event,
            "Ticket": Ticket,
            "Booking": Booking,
            "Payment": Payment,
            "Organization": Organization,
            "TicketType": TicketType,
            "Count": Count,
            "Sum": Sum,
            "Q": Q,
            "F": F,
            "timezone": timezone,
        }

        result = eval(query_code, {"__builtins__": {}}, safe_namespace)

        if hasattr(result, "__iter__") and not isinstance(result, (str, dict)):
            if hasattr(result, "count"):
                return list(result.values())[:100]
            return list(result)[:100]
        elif hasattr(result, "__dict__"):
            return {
                k: str(v) for k, v in result.__dict__.items() if not k.startswith("_")
            }
        else:
            return result

    except Exception as e:
        logger.error(f"Query execution error: {str(e)}\nQuery: {query_code}")
        return {"error": str(e), "query": query_code}


def generate_event_description(
    title: str, category: str, location: str, date: str, details: str = ""
) -> dict:
    prompt = f"""Generate a compelling event description in English and French for:

Title: {title}
Category: {category}
Location: {location}
Date: {date}
Additional Details: {details}

Requirements:
- Make it engaging and professional
- Highlight key benefits for attendees
- Include a call-to-action
- Keep it under 300 words
- NO emojis

Return as JSON:
{{"description_en": "...", "description_fr": "..."}}"""
    return gemini.generate_json(prompt, 2048)


def generate_social_posts(
    event_title: str, event_date: str, event_location: str, ticket_price: str = ""
) -> dict:
    prompt = f"""Create 3 social media posts for this event:

Event: {event_title}
Date: {event_date}
Location: {event_location}
Price: {ticket_price}

Generate posts for:
1. Twitter/X (max 280 chars, include hashtags)
2. Facebook (engaging, can be longer)
3. Instagram (visual-focused, include emoji)

Return as JSON:
{{"twitter": "...", "facebook": "...", "instagram": "..."}}"""
    return gemini.generate_json(prompt)


def generate_email_template(event_title: str, event_details: dict) -> dict:
    prompt = f"""Create an event invitation email template:

Event: {event_title}
Details: {json.dumps(event_details)}

Include:
- Catchy subject line
- Engaging opening
- Event highlights
- Clear CTA to buy tickets
- Professional closing

Return as JSON:
{{"subject": "...", "body_html": "...", "body_text": "..."}}"""
    return gemini.generate_json(prompt)


SUPPORT_SYSTEM_PROMPT = """You are Reckot's AI Assistant with DATABASE QUERY capabilities. Reckot is an event ticketing platform in Cameroon.

IMPORTANT SCOPE: You ONLY answer questions about Reckot and its features (events, tickets, payments, organizations, check-in, etc.).
REFUSE to answer general knowledge questions, trivia, or topics unrelated to Reckot. If asked about unrelated topics, politely respond: "I can only help with questions about Reckot, our event ticketing platform. How can I assist you with events, tickets, payments, or check-in?"

Event Search Questions:
When users ask about finding specific types of events (e.g., "any cake events?", "food events near me?", "music concerts?"), EXECUTE a query to search for matching events.
- Search in BOTH title and description fields using Q objects
- ALWAYS filter is_public=True and state='PUBLISHED'
- Limit results to 5 events using [:5]
- Use .values() to get required fields including organization__slug
- Example for single keyword: {{"action": "execute_query", "query": "list(Event.objects.filter(Q(title__icontains='cake') | Q(description__icontains='cake'), is_public=True, state='PUBLISHED').values('title', 'slug', 'organization__slug', 'start_at', 'location')[:5])"}}
- For multiple keywords (e.g. "food or cake"), search for the primary keyword only
- You will receive a list of event dictionaries
- Format each event as: **[Event Title](/events/org-slug/event-slug/)** - Location, Date
- Build URL using: /events/{{organization__slug}}/{{slug}}/
- If no events found, suggest they [browse all events](/events/discover/)

When users ask questions about data (counts, statistics, totals, etc.), you MUST:
1. Generate a Django ORM query to fetch the actual data
2. Return the query in this JSON format: {{"action": "execute_query", "query": "YourModel.objects.filter(...).count()"}}
3. For events, ALWAYS use is_public=True to exclude private events
4. For organizations, only show public data
5. Never expose private user information without authentication

Available Models and Fields:
{schema}

Query Examples:
- "How many events?" → {{"action": "execute_query", "query": "Event.objects.filter(is_public=True).count()"}}
- "Total tickets sold?" → {{"action": "execute_query", "query": "Ticket.objects.filter(status='VALID').count()"}}
- "Revenue this month?" → {{"action": "execute_query", "query": "Payment.objects.filter(status='COMPLETED', created_at__month=timezone.now().month).aggregate(total=Sum('amount'))['total'] or 0"}}

Rules:
- ALWAYS filter is_public=True for events (exclude private)
- Use Django ORM syntax only
- No SQL, only Python/Django ORM
- Keep queries simple and safe
- Return single value or simple aggregate

Authentication & Access Control:
- Check User Context for user_id/user_email
- If missing, user is NOT logged in
- Public data only: Event counts, Organization counts (where is_public=True)
- Private data requires authentication:
  * Payments: MUST filter by user (booking__event__organization__members__id=user_id)
  * Tickets: MUST scope to user's events/bookings
  * Withdrawals: MUST filter by user's organization
  * Analytics: MUST scope to user's events
- NEVER query private data without authentication
- NEVER expose other users' data
- If user asks for private data while unauthenticated: "Please [log in to your account](/accounts/login/) to view this information"

Response Formatting:
- Use markdown for links: [text](url)
- Common page links to use in responses:
  * Login: [log in to your account](/accounts/login/)
  * Browse/discover events: [browse events](/events/discover/) or [discover events](/events/discover/)
  * Create event: [create a new event](/events/create/)
  * Dashboard/Reports: [your dashboard](/reports/) or [analytics dashboard](/reports/)
  * Events list: [your events](/events/)
  * My tickets: [view your tickets](/tickets/my/)
  * Bookings/tickets list: [view your bookings](/tickets/)
  * Organizations: [manage your organization](/orgs/)
  * Settings: [account settings](/app/settings/)
- When user asks about specific event types (food, music, tech, etc.), suggest they [search for events on the discover page](/events/discover/)
- Format responses with **bold** and *italic* where appropriate
- Use code blocks with backticks for technical details

For support tickets:
{{"action": "create_ticket", "category": "PAYMENT|TICKET|EVENT|OTHER", "priority": "LOW|MEDIUM|HIGH|URGENT", "subject": "...", "description": "..."}}

Be concise and accurate."""


def chat_with_assistant(
    user_message: str, conversation_history: list, context: Optional[dict] = None
) -> dict:
    context_str = (
        f"\n\nUser Context:\n{json.dumps(context, indent=2)}" if context else ""
    )

    history_str = "\n".join(
        [
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in conversation_history[-10:]
        ]
    )

    schema = get_model_schema()
    schema_str = json.dumps(schema, indent=2)

    prompt = f"""{SUPPORT_SYSTEM_PROMPT.format(schema=schema_str)}
{context_str}

Conversation History:
{history_str}

User: {user_message}

If this is a data question, respond with execute_query action. Otherwise provide helpful text."""

    response = gemini.generate(prompt)
    result = {"message": response, "action": None}

    try:
        if '{"action": "execute_query"' in response:
            start = response.find('{"action": "execute_query"')
            end = response.find("}", start) + 1
            query_data = json.loads(response[start:end])
            query_code = query_data.get("query", "")

            query_result = execute_django_query(query_code)

            if isinstance(query_result, dict) and "error" in query_result:
                result["message"] = (
                    f"I encountered an error executing the query: {query_result['error']}"
                )
            else:
                if isinstance(query_result, list) and len(query_result) > 0:
                    if all(isinstance(item, dict) and 'slug' in item and 'organization__slug' in item for item in query_result):
                        formatted_events = []
                        for event in query_result:
                            title = event.get('title', 'Untitled Event')
                            org_slug = event.get('organization__slug', '')
                            event_slug = event.get('slug', '')
                            location = event.get('location', '')
                            start_at = event.get('start_at', '')

                            event_url = f"/events/{org_slug}/{event_slug}/"
                            event_line = f"**[{title}]({event_url})**"
                            if location or start_at:
                                details = []
                                if location:
                                    details.append(location)
                                if start_at:
                                    from datetime import datetime
                                    try:
                                        if isinstance(start_at, str):
                                            date_obj = datetime.fromisoformat(start_at.replace('Z', '+00:00'))
                                        else:
                                            date_obj = start_at
                                        details.append(date_obj.strftime('%b %d, %Y'))
                                    except (ValueError, AttributeError, TypeError):
                                        pass
                                event_line += f" - {', '.join(details)}"
                            formatted_events.append(event_line)

                        result["message"] = f"I found {len(formatted_events)} event{'s' if len(formatted_events) != 1 else ''}:\n\n" + "\n".join(formatted_events)
                    else:
                        result["message"] = f"Result: {query_result}"
                else:
                    if isinstance(query_result, list) and len(query_result) == 0:
                        result["message"] = "I couldn't find any events matching your search. You can [browse all events](/discover/) to see what's available!"
                    else:
                        result["message"] = f"Result: {query_result}"
                result["action"] = "execute_query"
                result["query_result"] = query_result

        elif '{"action": "create_ticket"' in response:
            start = response.find('{"action": "create_ticket"')
            end = response.find("}", start) + 1
            ticket_data = json.loads(response[start:end])
            result["action"] = "create_ticket"
            result["ticket_data"] = ticket_data
            result["message"] = (
                response[:start].strip()
                if start > 0
                else "I'll create a support ticket for you."
            )
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nResponse: {response}")
        pass

    return result


def analyze_issue(issue_description: str, error_logs: str = "") -> dict:
    prompt = f"""Analyze this technical issue and provide debugging suggestions:

Issue: {issue_description}
Error Logs: {error_logs}

Provide:
1. Likely cause
2. Suggested solutions (step by step)
3. Whether this needs human support (yes/no)
4. Priority level (LOW/MEDIUM/HIGH/URGENT)

Return as JSON:
{{"cause": "...", "solutions": ["..."], "needs_human": true/false, "priority": "...", "summary": "..."}}"""

    result = gemini.generate_json(prompt)
    if "error" in result:
        return {
            "cause": "Unable to analyze",
            "solutions": [],
            "needs_human": True,
            "priority": "MEDIUM",
            "summary": result.get("raw", ""),
        }
    return result


def analyze_event_performance(event_data: dict) -> str:
    prompt = f"""Analyze this event's performance data and provide actionable insights:

Event Data:
{json.dumps(event_data, indent=2)}

Provide:
1. 3-5 key insights about ticket sales and attendance
2. Recommendations for improvement
3. Comparison to typical events (if possible)
4. Predicted final attendance

Format as clear, actionable bullet points. NO emojis."""
    return gemini.generate(prompt)


def suggest_pricing(event_details: dict, market_data: Optional[dict] = None) -> str:
    prompt = f"""Suggest optimal ticket pricing for this event:

Event Details:
{json.dumps(event_details, indent=2)}

Market Context:
{json.dumps(market_data or {}, indent=2)}

Consider:
- Event type and target audience
- Location and venue costs
- Competitor pricing
- Early bird vs regular pricing strategy

Provide specific price recommendations in XAF with reasoning."""
    return gemini.generate(prompt)
