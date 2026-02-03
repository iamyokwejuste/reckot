import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    agent_name: str
    role: str
    content: str
    timestamp: str
    emoji: str
    metadata: Dict[str, Any] = None


@dataclass
class AgentPersona:
    name: str
    role: str
    system_prompt: str
    specialization: str
    emoji: str


class EventConciergeOrchestrator:

    def __init__(self):
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-3-flash-preview")
        self._client = None
        self.agents = self._load_agents()

    def _load_prompt(self, filename: str) -> str:
        prompt_path = Path(settings.BASE_DIR) / 'static' / 'markdown' / filename
        return prompt_path.read_text(encoding='utf-8')

    def _load_agents(self) -> Dict[str, AgentPersona]:
        return {
            "analyst": AgentPersona(
                name="Event Analyst",
                role="Data Analysis & Insights",
                emoji="📊",
                specialization="event performance metrics",
                system_prompt=self._load_prompt('agent_analyst.md')
            ),
            "marketer": AgentPersona(
                name="Marketing Strategist",
                role="Campaign Development",
                emoji="🎯",
                specialization="marketing campaigns and audience engagement",
                system_prompt=self._load_prompt('agent_marketer.md')
            ),
            "support": AgentPersona(
                name="Customer Success Agent",
                role="Attendee Experience",
                emoji="💬",
                specialization="customer support and attendee satisfaction",
                system_prompt=self._load_prompt('agent_support.md')
            ),
            "fraud_detective": AgentPersona(
                name="Fraud Detective",
                role="Security & Verification",
                emoji="🔍",
                specialization="fraud detection and event security",
                system_prompt=self._load_prompt('agent_fraud.md')
            ),
            "pricing_optimizer": AgentPersona(
                name="Pricing Optimizer",
                role="Revenue Strategy",
                emoji="💰",
                specialization="pricing strategy and revenue optimization",
                system_prompt=self._load_prompt('agent_pricing.md')
            ),
        }

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        return self._client

    def _generate_agent_response(
        self,
        agent_persona: AgentPersona,
        context: str,
        conversation_history: List[AgentMessage] = None
    ) -> Optional[str]:
        if not self.client:
            logger.warning("Gemini client not available")
            return None

        history_text = ""
        if conversation_history:
            history_text = "\n\n".join([
                f"{msg.emoji} **{msg.agent_name}** ({msg.role}):\n{msg.content}"
                for msg in conversation_history[-5:]
            ])

        prompt = f"""{agent_persona.system_prompt}

EVENT CONTEXT:
{context}

{"PREVIOUS DISCUSSION:\n" + history_text if history_text else ""}

As {agent_persona.name}, provide expert analysis on {agent_persona.specialization}. Keep response concise (2-4 paragraphs), actionable. Start with key insight, then specific recommendations."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"max_output_tokens": 1024, "temperature": 0.8},
            )
            return response.text
        except Exception as e:
            logger.error(f"Agent {agent_persona.name} generation error: {e}")
            return None

    def orchestrate_discussion(
        self,
        event_data: Dict[str, Any],
        focus_areas: List[str] = None
    ) -> List[AgentMessage]:
        if focus_areas is None:
            focus_areas = ["analyst", "marketer", "support", "fraud_detective", "pricing_optimizer"]

        context = self._build_event_context(event_data)
        conversation_history = []

        logger.info(f"Multi-agent discussion: {event_data.get('title')}")

        for agent_key in focus_areas:
            agent = self.agents.get(agent_key)
            if not agent:
                continue

            response = self._generate_agent_response(
                agent_persona=agent,
                context=context,
                conversation_history=conversation_history
            )

            if response:
                message = AgentMessage(
                    agent_name=agent.name,
                    role=agent.role,
                    content=response,
                    timestamp="now",
                    emoji=agent.emoji,
                    metadata={"agent_key": agent_key}
                )
                conversation_history.append(message)

        return conversation_history

    def _build_event_context(self, event_data: Dict[str, Any]) -> str:
        context_parts = [f"EVENT: {event_data.get('title', 'N/A')}"]

        if event_data.get('description'):
            context_parts.append(f"\nDESCRIPTION:\n{event_data['description'][:500]}...")

        details = []
        if event_data.get('location'):
            details.append(f"Location: {event_data['location']}")
        if event_data.get('start_date'):
            details.append(f"Date: {event_data['start_date']}")
        if event_data.get('category'):
            details.append(f"Category: {event_data['category']}")
        if event_data.get('capacity'):
            details.append(f"Capacity: {event_data['capacity']}")

        if details:
            context_parts.append("\n" + " | ".join(details))

        if event_data.get('metrics'):
            metrics = event_data['metrics']
            context_parts.append(f"\n\nMETRICS:")
            context_parts.append(f"- Tickets Sold: {metrics.get('tickets_sold', 0)}")
            context_parts.append(f"- Revenue: {metrics.get('revenue', 0):,} XAF")
            context_parts.append(f"- Attendance Rate: {metrics.get('attendance_rate', 0)}%")
            context_parts.append(f"- Conversion Rate: {metrics.get('conversion_rate', 0)}%")
            context_parts.append(f"- Days Until Event: {metrics.get('days_until_event', 'N/A')}")

        if event_data.get('ticket_types'):
            context_parts.append(f"\n\nTICKET TYPES:")
            for ticket in event_data['ticket_types']:
                context_parts.append(
                    f"- {ticket['name']}: {ticket['price']:,} XAF "
                    f"({ticket.get('sold', 0)}/{ticket.get('quantity', 'unlimited')} sold)"
                )

        if event_data.get('booking_patterns'):
            context_parts.append(f"\n\nBOOKING PATTERNS:")
            patterns = event_data['booking_patterns']
            if patterns.get('peak_hours'):
                context_parts.append(f"- Peak booking hours: {patterns['peak_hours']}")
            if patterns.get('popular_ticket'):
                context_parts.append(f"- Most popular ticket: {patterns['popular_ticket']}")
            if patterns.get('refund_rate'):
                context_parts.append(f"- Refund rate: {patterns['refund_rate']}%")

        return "\n".join(context_parts)

    def get_agent_opinion(
        self,
        agent_key: str,
        event_data: Dict[str, Any],
        specific_question: str = None
    ) -> Optional[str]:
        agent = self.agents.get(agent_key)
        if not agent:
            logger.error(f"Unknown agent: {agent_key}")
            return None

        context = self._build_event_context(event_data)
        if specific_question:
            context += f"\n\nSPECIFIC QUESTION:\n{specific_question}"

        return self._generate_agent_response(agent_persona=agent, context=context)

    def quick_audit(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        messages = self.orchestrate_discussion(event_data)

        return {
            "event_title": event_data.get("title"),
            "audit_timestamp": "now",
            "agent_count": len(messages),
            "recommendations": [
                {
                    "agent": msg.agent_name,
                    "role": msg.role,
                    "analysis": msg.content,
                    "emoji": msg.emoji
                }
                for msg in messages
            ]
        }


event_concierge = EventConciergeOrchestrator()
