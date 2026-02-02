import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.checkin.models import CheckIn, SwagCollection
from apps.checkin.queries import get_event_swag_items
from apps.checkin.services import verify_and_checkin, collect_swag
from apps.events.models import Event
from apps.tickets.models import Ticket

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
class OfflineDataView(View):
    def get(self, request, org_slug, event_slug):
        try:
            event = Event.objects.get(slug=event_slug, organization__slug=org_slug)

            if not event.organization.members.filter(id=request.user.id).exists():
                return JsonResponse({"error": "Permission denied"}, status=403)

            tickets = list(
                Ticket.objects.filter(booking__event=event)
                .select_related("ticket_type", "booking__user")
                .values(
                    "id",
                    "code",
                    "attendee_name",
                    "attendee_email",
                    "is_checked_in",
                    "checked_in_at",
                    "ticket_type__name",
                    "ticket_type__price",
                    "booking__user__email",
                    "booking__user__first_name",
                    "booking__user__last_name",
                )
            )

            for ticket in tickets:
                ticket["eventId"] = event.id
                if ticket["checked_in_at"]:
                    ticket["checked_in_at"] = ticket["checked_in_at"].isoformat()

            swag_items = list(
                get_event_swag_items(event.id).values(
                    "id", "name", "description", "quantity"
                )
            )
            for item in swag_items:
                item["eventId"] = event.id

            return JsonResponse(
                {
                    "event": {
                        "id": event.id,
                        "slug": event.slug,
                        "title": event.title,
                        "start_time": event.start_time.isoformat(),
                        "end_time": event.end_time.isoformat(),
                    },
                    "tickets": tickets,
                    "swagItems": swag_items,
                }
            )

        except Event.DoesNotExist:
            return JsonResponse({"error": "Event not found"}, status=404)
        except Exception as e:
            logger.error(f"Error fetching offline data: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(login_required, name="dispatch")
class SyncCheckinView(View):
    def post(self, request):
        try:
            import json

            data = json.loads(request.body)
            ticket_code = data.get("ticketCode")
            notes = data.get("notes", "")

            if not ticket_code:
                return JsonResponse({"error": "Ticket code required"}, status=400)

            result = verify_and_checkin(ticket_code, request.user)

            if "error" in result:
                return JsonResponse(
                    {"success": False, "message": result["error"]}, status=400
                )

            checkin = result["checkin"]
            return JsonResponse(
                {
                    "success": True,
                    "reference": str(checkin.reference),
                    "ticket": {
                        "code": result["ticket"].code,
                        "attendeeName": result["ticket"].attendee_name,
                        "isCheckedIn": True,
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error syncing check-in: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(login_required, name="dispatch")
class SyncSwagCollectionView(View):
    def post(self, request):
        try:
            import json

            data = json.loads(request.body)
            ticket_code = data.get("ticketCode")
            swag_item_id = data.get("swagItemId")

            if not ticket_code or not swag_item_id:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            checkin = CheckIn.objects.filter(
                ticket__code=ticket_code
            ).select_related("ticket").first()

            if not checkin:
                return JsonResponse({"error": "Check-in not found"}, status=404)

            result = collect_swag(checkin.id, swag_item_id)

            if "error" in result:
                return JsonResponse({"error": result["error"]}, status=400)

            return JsonResponse({"success": True})

        except Exception as e:
            logger.error(f"Error syncing swag collection: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)
