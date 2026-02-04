import json
import logging
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from google import genai
from django.conf import settings

from django.utils.html import strip_tags

from django.contrib.auth import get_user_model

User = get_user_model()

_ai_query_service = None

def _get_ai_query_service():
    global _ai_query_service
    if _ai_query_service is None:
        from apps.ai.services.ai_query_service import AIQueryService
        _ai_query_service = AIQueryService()
    return _ai_query_service

logger = logging.getLogger(__name__)


def clean_html_content(html_text: str) -> str:
    if not html_text:
        return ""
    text = strip_tags(html_text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


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






def generate_event_description(
    title: str, category: str, location: str, date: str, details: str = ""
) -> dict:
    template = _load_prompt('event_description.md')
    prompt = _format_prompt(template, title=title, category=category, location=location, date=date, details=details)
    return gemini.generate_json(prompt, 2048)


def generate_social_posts(
    event_title: str, event_date: str, event_location: str, ticket_price: str = ""
) -> dict:
    template = _load_prompt('social_posts.md')
    prompt = _format_prompt(template, event_title=event_title, event_date=event_date, event_location=event_location, ticket_price=ticket_price)
    return gemini.generate_json(prompt)


def generate_email_template(event_title: str, event_details: dict) -> dict:
    template = _load_prompt('email_template.md')
    prompt = _format_prompt(template, event_title=event_title, event_details=json.dumps(event_details))
    return gemini.generate_json(prompt)


def _load_prompt(filename: str) -> str:
    prompt_path = Path(settings.BASE_DIR) / 'static' / 'markdown' / filename
    return prompt_path.read_text(encoding='utf-8')


def _format_prompt(template: str, **kwargs) -> str:
    return template.format(**kwargs)


SUPPORT_SYSTEM_PROMPT = _load_prompt('support_assistant.md')


def _format_query_result(result):
    if result is None:
        return "No data found."

    if isinstance(result, (int, float)):
        return f"**{result:,}**"

    if isinstance(result, str):
        return result

    if isinstance(result, Decimal):
        return f"**{float(result):,.2f} XAF**"

    if isinstance(result, dict):
        if len(result) == 1:
            key, value = next(iter(result.items()))
            if isinstance(value, Decimal):
                return f"**{float(value):,.2f} XAF**"
            elif isinstance(value, (int, float)):
                return f"**{value:,}**"

        lines = []
        for key, value in result.items():
            if key.startswith('_'):
                continue
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, Decimal):
                formatted_value = f"{float(value):,.2f} XAF"
            elif isinstance(value, (int, float)):
                formatted_value = f"{value:,}"
            else:
                formatted_value = str(value)
            lines.append(f"**{formatted_key}:** {formatted_value}")
        return "\n".join(lines) if lines else str(result)

    if isinstance(result, list):
        if not result:
            return "No results found."

        if all(isinstance(item, dict) for item in result):
            formatted_items = []
            for item in result:
                parts = []
                for key, value in item.items():
                    if key.startswith('_'):
                        continue
                    if isinstance(value, Decimal):
                        parts.append(f"**{key.replace('_', ' ').title()}:** {float(value):,.2f} XAF")
                    elif isinstance(value, (int, float)):
                        parts.append(f"**{key.replace('_', ' ').title()}:** {value:,}")
                    else:
                        parts.append(f"**{key.replace('_', ' ').title()}:** {value}")
                formatted_items.append(" | ".join(parts))
            return "\n".join(formatted_items)

        return "\n".join([f"• {_format_query_result(item)}" for item in result[:10]])

    return str(result)


def chat_with_assistant(
    user_message: str, conversation_history: list, context: Optional[dict] = None
) -> dict:
    ai_service = _get_ai_query_service()

    user = None
    if context:
        user_id = context.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass

    context_str = ""
    if context:
        safe_context = {k: v for k, v in context.items() if k != 'user_id'}
        context_str = f"\n\nUser Context:\n{json.dumps(safe_context, indent=2)}"

    history_str = "\n".join(
        [
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in conversation_history[-10:]
        ]
    )

    prompt = f"""{SUPPORT_SYSTEM_PROMPT}
        {context_str}

        Conversation History:
        {history_str}

        User: {user_message}"""

    response = gemini.generate(prompt, max_tokens=2048)
    result = {"message": response, "action": None}

    try:
        is_data_question = any(keyword in user_message.lower() for keyword in [
            'how many', 'count', 'total', 'list', 'show', 'find', 'search',
            'latest', 'recent', 'last', 'events', 'tickets', 'revenue'
        ])

        if '{"action": "execute_query"' in response or is_data_question:
            query_response = ai_service.answer_question(user_message, user)

            if not query_response['success']:
                result["message"] = f"I encountered an error: {query_response.get('error', 'Unknown error')}"
            else:
                query_result = query_response.get('data', [])

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
                        result["message"] = _format_query_result(query_result)
                else:
                    if isinstance(query_result, list) and len(query_result) == 0:
                        result["message"] = "I couldn't find any events matching your search. You can [browse all events](/events/discover/) to see what's available!"
                    else:
                        result["message"] = _format_query_result(query_result)
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
    except Exception as e:
        logger.error(f"Error in chat_with_assistant: {str(e)}", exc_info=True)
        result["message"] = "Sorry, I encountered an error processing your request."

    return result


def analyze_issue(issue_description: str, error_logs: str = "") -> dict:
    template = _load_prompt('issue_analysis.md')
    prompt = _format_prompt(template, issue_description=issue_description, error_logs=error_logs)
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
    template = _load_prompt('event_performance.md')
    prompt = _format_prompt(template, event_data=json.dumps(event_data, indent=2))
    return gemini.generate(prompt)


def suggest_pricing(event_details: dict, market_data: Optional[dict] = None) -> str:
    template = _load_prompt('pricing_suggestion.md')
    prompt = _format_prompt(template, event_details=json.dumps(event_details, indent=2), market_data=json.dumps(market_data or {}, indent=2))
    return gemini.generate(prompt)
