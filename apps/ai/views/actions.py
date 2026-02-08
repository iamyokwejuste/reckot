import json
import logging
import base64
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Sum
from django.conf import settings

from apps.ai.models import SupportTicket, AIConversation, AIMessage
from apps.ai import services
from apps.ai.utils.decorators import (
    ai_feature_required,
    ai_rate_limit,
    log_ai_usage,
    validate_query,
)
from apps.events.models import Event
from apps.core.services.ai import gemini_ai

logger = logging.getLogger(__name__)


@method_decorator(ai_feature_required, name="dispatch")
class AIAssistantView(View):
    template_name = "ai/assistant.html"

    def get(self, request, session_id=None):
        conversation = None
        messages_list = []

        if session_id:
            conversation = AIConversation.objects.filter(session_id=session_id).first()
            if conversation:
                messages_list = [
                    {"role": m.role, "content": m.content}
                    for m in conversation.messages.all()
                ]

        context = self._build_user_context(request)

        return render(
            request,
            self.template_name,
            {
                "conversation": conversation,
                "chat_messages": json.dumps(messages_list),
                "context": context,
                "session_id": session_id,
            },
        )

    def _build_user_context(self, request):
        context = {}
        if request.user.is_authenticated:
            context["user_name"] = request.user.get_full_name() or request.user.username
            context["is_authenticated"] = True
        return context


@method_decorator(
    [
        csrf_exempt,
        ai_feature_required,
        ai_rate_limit(30),
        log_ai_usage("CHAT"),
        validate_query,
    ],
    name="dispatch",
)
class AIAssistantChatView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({"error": str(_("Invalid JSON"))}, status=400)

        user_message = data.get("message", "").strip()
        session_id = data.get("session_id")

        if not user_message:
            return JsonResponse({"error": str(_("Message is required"))}, status=400)

        word_count = len(user_message.split())
        if word_count > 50:
            return JsonResponse(
                {"error": str(_("Message too long. Please limit to 50 words or less."))},
                status=400,
            )

        if request.user.is_authenticated:
            today_start = timezone.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            user_messages_today = AIMessage.objects.filter(
                conversation__user=request.user,
                role=AIMessage.Role.USER,
                created_at__gte=today_start,
            ).count()

            daily_limit = getattr(settings, "RECKOT_AI_CHAT_DAILY_LIMIT", 50)
            if user_messages_today >= daily_limit:
                return JsonResponse(
                    {
                        "error": str(_("Daily chat limit reached. You can send up to %(daily_limit)s messages per day. Please try again tomorrow.") % {"daily_limit": daily_limit})
                    },
                    status=429,
                )

        conversation = self._get_or_create_conversation(request, session_id)
        history = self._get_conversation_history(conversation)
        context = self._build_context(request)

        AIMessage.objects.create(
            conversation=conversation, role=AIMessage.Role.USER, content=user_message
        )

        try:
            result = services.chat_with_assistant(user_message, history, context)
            logger.info(f"AI response: {result}")

            if result.get("action") == "create_ticket":
                ticket = self._create_ticket(
                    request, result.get("ticket_data", {}), conversation
                )
                result["ticket_reference"] = str(ticket.reference)
                result["message"] += f"\n\nTicket created: #{ticket.reference}"

            AIMessage.objects.create(
                conversation=conversation,
                role=AIMessage.Role.ASSISTANT,
                content=result["message"],
                metadata={"action": result.get("action")},
            )

            return JsonResponse(
                {
                    "message": result["message"],
                    "action": result.get("action"),
                    "ticket_reference": result.get("ticket_reference"),
                    "query_result": result.get("query_result"),
                    "session_id": str(conversation.session_id),
                }
            )
        except Exception as e:
            logger.error(f"Error in AI chat: {str(e)}", exc_info=True)
            return JsonResponse(
                {
                    "error": str(_("An error occurred processing your request")),
                    "message": str(_("Sorry, I encountered an error. Please try again.")),
                },
                status=500,
            )

    def _get_or_create_conversation(self, request, session_id=None):
        if session_id:
            conversation = AIConversation.objects.filter(session_id=session_id).first()
            if conversation:
                return conversation

        conversation = AIConversation.objects.create(
            user=request.user if request.user.is_authenticated else None
        )
        return conversation

    def _get_conversation_history(self, conversation):
        return [
            {"role": m.role.lower(), "content": m.content}
            for m in conversation.messages.all()[:20]
        ]

    def _build_context(self, request):
        context = {"timestamp": timezone.now().isoformat()}
        if request.user.is_authenticated:
            context["is_authenticated"] = True
            context["user_name"] = request.user.get_full_name() or request.user.username
        return context

    def _create_ticket(self, request, ticket_data, conversation):
        return SupportTicket.objects.create(
            user=request.user if request.user.is_authenticated else None,
            subject=ticket_data.get("subject", "Support Request"),
            description=ticket_data.get("description", ""),
            category=ticket_data.get("category", SupportTicket.Category.OTHER),
            priority=ticket_data.get("priority", SupportTicket.Priority.MEDIUM),
            ai_summary=f"Created via AI Assistant. Session: {conversation.session_id}",
        )


@method_decorator(
    [ai_feature_required, ai_rate_limit(30), log_ai_usage("GENERATE_DESCRIPTION")],
    name="dispatch",
)
class AIGenerateContentView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": str(_("Invalid JSON"))}, status=400)

        content_type = data.get("type", "description")

        generators = {
            "description": self._generate_description,
            "social": self._generate_social,
            "email": self._generate_email,
        }

        generator = generators.get(content_type)
        if not generator:
            return JsonResponse({"error": str(_("Invalid content type"))}, status=400)

        result = generator(data)
        return JsonResponse(result)

    def _generate_description(self, data):
        return services.generate_event_description(
            title=data.get("title", ""),
            category=data.get("category", ""),
            location=data.get("location", ""),
            date=data.get("date", ""),
            details=data.get("details", ""),
        )

    def _generate_social(self, data):
        return services.generate_social_posts(
            event_title=data.get("title", ""),
            event_date=data.get("date", ""),
            event_location=data.get("location", ""),
            ticket_price=data.get("price", ""),
        )

    def _generate_email(self, data):
        return services.generate_email_template(
            event_title=data.get("title", ""), event_details=data
        )


@method_decorator(
    [ai_feature_required, ai_rate_limit(30), log_ai_usage("INSIGHT")], name="dispatch"
)
class AIAnalyzeIssueView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": str(_("Invalid JSON"))}, status=400)

        result = services.analyze_issue(
            issue_description=data.get("issue", ""), error_logs=data.get("logs", "")
        )
        return JsonResponse(result)


@method_decorator(
    [ai_feature_required, ai_rate_limit(30), log_ai_usage("INSIGHT")], name="dispatch"
)
class AIEventInsightsView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        if not event.organization.members.filter(id=request.user.id).exists():
            return JsonResponse({"error": str(_("Permission denied"))}, status=403)

        event_data = {
            "title": event.title,
            "date": str(event.start_at),
            "location": event.location,
            "capacity": event.capacity,
            "tickets_sold": event.bookings.filter(status="CONFIRMED").count(),
            "total_revenue": float(
                event.bookings.filter(status="CONFIRMED").aggregate(
                    total=Sum("total_amount")
                )["total"]
                or 0
            ),
        }

        insights = services.analyze_event_performance(event_data)
        return JsonResponse({"insights": insights, "event_data": event_data})


class SupportTicketListView(LoginRequiredMixin, View):
    def get(self, request):
        tickets = SupportTicket.objects.filter(user=request.user)
        return render(request, "ai/tickets/list.html", {"tickets": tickets})


class SupportTicketDetailView(LoginRequiredMixin, View):
    def get(self, request, reference):
        ticket = get_object_or_404(
            SupportTicket, reference=reference, user=request.user
        )
        return render(request, "ai/tickets/detail.html", {"ticket": ticket})


class SupportTicketCreateView(View):
    def get(self, request):
        return render(request, "ai/tickets/create.html")

    def post(self, request):
        ticket = SupportTicket.objects.create(
            user=request.user if request.user.is_authenticated else None,
            guest_email=request.POST.get("email", ""),
            subject=request.POST.get("subject", ""),
            description=request.POST.get("description", ""),
            category=request.POST.get("category", SupportTicket.Category.OTHER),
            priority=SupportTicket.Priority.MEDIUM,
        )

        if services.gemini.is_available():
            analysis = services.analyze_issue(ticket.description)
            ticket.ai_summary = analysis.get("summary", "")
            ticket.ai_suggested_solution = "\n".join(analysis.get("solutions", []))
            ticket.priority = analysis.get("priority", SupportTicket.Priority.MEDIUM)
            ticket.save()

        messages.success(request, _("Ticket #%(reference)s created successfully.") % {"reference": ticket.reference})
        return redirect("ai:ticket_detail", reference=ticket.reference)


@method_decorator(csrf_exempt, name="dispatch")
class ClearConversationView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            session_id = data.get("session_id")
        except json.JSONDecodeError:
            session_id = None

        if session_id:
            # Delete the conversation by session_id
            deleted_count, _ = AIConversation.objects.filter(
                session_id=session_id
            ).delete()
            logger.info(
                f"Deleted conversation with session_id {session_id}: {deleted_count} records"
            )
            return JsonResponse({"status": "ok", "deleted": deleted_count})
        else:
            # If no session_id, delete all conversations for the authenticated user
            if request.user.is_authenticated:
                deleted_count, _ = AIConversation.objects.filter(
                    user=request.user
                ).delete()
                logger.info(
                    f"Deleted all conversations for user {request.user.id}: {deleted_count} records"
                )
                return JsonResponse({"status": "ok", "deleted": deleted_count})

        return JsonResponse({"status": "ok", "deleted": 0})


@method_decorator([csrf_exempt, ai_feature_required], name="dispatch")
class AudioTranscribeView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            audio_base64 = data.get("audio")
            mime_type = data.get("mimeType", "audio/webm")

            if not audio_base64:
                return JsonResponse({"error": str(_("No audio data provided"))}, status=400)

            audio_data = base64.b64decode(audio_base64)

            prompt = "Transcribe this audio clearly and accurately. Only output the transcribed text, nothing else."
            transcription = gemini_ai.chat_with_audio(prompt, audio_data, mime_type)

            if not transcription:
                return JsonResponse({"error": str(_("Transcription failed"))}, status=500)

            return JsonResponse({"transcription": transcription.strip()})

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
            return JsonResponse(
                {"error": str(_("Transcription failed: %(error)s") % {"error": str(e)})}, status=500
            )
