import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify

from apps.cfp.models import CallForProposals
from apps.core.services.ai import gemini_ai
from apps.events.models import Event
from apps.events.services.event_service import create_event
from apps.orgs.models import Membership, MemberRole, Organization
from apps.tickets.models import TicketType

logger = logging.getLogger(__name__)

EVENT_VISUALS = {
    "IN_PERSON": "modern event venue, professional setup, welcoming atmosphere",
    "ONLINE": "digital workspace, virtual conference, screen-based presentation",
    "HYBRID": "modern venue with screens and cameras, hybrid event setup",
}


def _get_user_organization(user):
    org = Organization.objects.filter(owner=user).first()
    if org:
        return org

    membership = (
        Membership.objects.filter(
            user=user, role__in=[MemberRole.ADMIN, MemberRole.MANAGER]
        )
        .select_related("organization")
        .first()
    )
    if membership:
        return membership.organization

    return None


def _find_event_by_title(user, event_title):
    return (
        Event.objects.filter(
            title__icontains=event_title, organization__members=user
        )
        .select_related("organization")
        .first()
    )


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        if timezone.is_naive(value):
            return timezone.make_aware(value)
        return value
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            return timezone.make_aware(dt)
        except (ValueError, TypeError):
            continue
    return None


def _generate_cover_image(event):
    try:
        visual_guide = EVENT_VISUALS.get(event.event_type, EVENT_VISUALS["IN_PERSON"])
        prompt = (
            f"Create a promotional event banner for: '{event.title}'. "
            f"{event.short_description or event.description[:120]}. "
            f"Visual style: {visual_guide}. "
            "Include bold, readable text with the event title prominently displayed. "
            "Professional advertising design, vibrant colors, modern African aesthetic, "
            "eye-catching typography. Aspect ratio 16:9, 1920x1080px. "
            "Design it like a professional event poster/flyer."
        )
        image_bytes = gemini_ai.generate_image(prompt)
        if image_bytes:
            filename = f"{slugify(event.title)}-cover.png"
            event.cover_image.save(filename, ContentFile(image_bytes), save=True)
            return True
    except Exception as e:
        logger.warning(f"Cover image generation failed for event {event.pk}: {e}")
    return False


def create_event_from_chat(user, data):
    if not user or not user.is_authenticated:
        return {"success": False, "error": "You must be logged in to create events."}

    org = _get_user_organization(user)
    if not org:
        return {
            "success": False,
            "error": "You don't have an organization. Please create one first at /orgs/.",
        }

    if not org.user_can(user, "create_events"):
        return {
            "success": False,
            "error": "You don't have permission to create events in this organization.",
        }

    title = data.get("title", "").strip()
    if not title:
        return {"success": False, "error": "Event title is required."}

    start_at = _parse_datetime(data.get("start_at"))
    end_at = _parse_datetime(data.get("end_at"))
    if not start_at or not end_at:
        return {"success": False, "error": "Valid start and end dates are required."}

    location = data.get("location", "")
    if not location:
        parts = [data.get("venue_name", ""), data.get("city", ""), data.get("country", "Cameroon")]
        location = ", ".join(p for p in parts if p)

    form_data = {
        "title": title,
        "description": data.get("description", title),
        "short_description": data.get("short_description", ""),
        "event_type": data.get("event_type", "IN_PERSON"),
        "start_at": start_at,
        "end_at": end_at,
        "timezone": data.get("timezone", "Africa/Douala"),
        "location": location,
        "venue_name": data.get("venue_name", ""),
        "city": data.get("city", ""),
        "country": data.get("country", "Cameroon"),
        "capacity": data.get("capacity", 100),
        "is_free": data.get("is_free", True),
        "contact_email": data.get("contact_email", user.email),
    }

    event, errors = create_event(user, org, form_data)
    if not event:
        error_msg = "; ".join(
            f"{k}: {', '.join(v)}" for k, v in (errors or {}).items()
        )
        return {"success": False, "error": error_msg or "Failed to create event."}

    created = ["Event"]
    cover_generated = _generate_cover_image(event)
    if cover_generated:
        created.append("cover image")

    cfp_data = data.get("cfp")
    if cfp_data and isinstance(cfp_data, dict):
        opens_at = _parse_datetime(cfp_data.get("opens_at")) or timezone.now()
        closes_at = _parse_datetime(cfp_data.get("closes_at"))
        if not closes_at:
            closes_at = event.start_at - timedelta(weeks=2)
            if closes_at <= timezone.now():
                closes_at = event.start_at
        try:
            CallForProposals.objects.create(
                event=event,
                title=cfp_data.get("title", "Call for proposals"),
                description=cfp_data.get("description", ""),
                status=CallForProposals.Status.DRAFT,
                opens_at=opens_at,
                closes_at=closes_at,
                max_submissions_per_speaker=cfp_data.get("max_submissions_per_speaker", 3),
                anonymous_review=cfp_data.get("anonymous_review", True),
            )
            created.append("CFP")
        except Exception as e:
            logger.warning(f"CFP creation failed for event {event.pk}: {e}")

    ticket_types_data = data.get("ticket_types")
    if ticket_types_data and isinstance(ticket_types_data, list):
        for tt in ticket_types_data:
            if not isinstance(tt, dict):
                continue
            name = tt.get("name", "").strip()
            if not name:
                continue
            try:
                price = Decimal(str(tt.get("price", 0)))
            except (InvalidOperation, ValueError):
                price = Decimal("0")
            try:
                TicketType.objects.create(
                    event=event,
                    name=name,
                    description=tt.get("description", ""),
                    price=price,
                    quantity=tt.get("quantity", 100),
                    max_per_order=tt.get("max_per_order", 10),
                    is_active=True,
                )
                created.append(f"ticket type \"{name}\"")
            except Exception as e:
                logger.warning(f"Ticket type creation failed for event {event.pk}: {e}")

    base_url = f"/events/{org.slug}/{event.slug}/"
    url = f"{base_url}dashboard/" if event.state != Event.State.PUBLISHED else base_url

    return {
        "success": True,
        "url": url,
        "title": event.title,
        "created": created,
    }


def create_cfp_from_chat(user, data):
    if not user or not user.is_authenticated:
        return {"success": False, "error": "You must be logged in to create a CFP."}

    event_title = data.get("event_title", "").strip()
    if not event_title:
        return {"success": False, "error": "Please specify which event to add the CFP to."}

    event = _find_event_by_title(user, event_title)
    if not event:
        return {
            "success": False,
            "error": f"Could not find an event matching \"{event_title}\". Please check the name.",
        }

    if not event.organization.user_can(user, "manage_cfp"):
        return {"success": False, "error": "You don't have permission to manage CFPs for this event."}

    if hasattr(event, "cfp"):
        return {
            "success": False,
            "error": f"\"{event.title}\" already has a CFP. You can configure it at /cfp/{event.organization.slug}/{event.slug}/config/",
        }

    opens_at = _parse_datetime(data.get("opens_at")) or timezone.now()
    closes_at = _parse_datetime(data.get("closes_at"))
    if not closes_at:
        closes_at = event.start_at if event.start_at else opens_at

    cfp = CallForProposals.objects.create(
        event=event,
        title=data.get("title", "Call for proposals"),
        description=data.get("description", ""),
        status=CallForProposals.Status.DRAFT,
        opens_at=opens_at,
        closes_at=closes_at,
        max_submissions_per_speaker=data.get("max_submissions_per_speaker", 3),
        anonymous_review=data.get("anonymous_review", True),
    )

    return {
        "success": True,
        "url": f"/cfp/{event.organization.slug}/{event.slug}/config/",
        "title": cfp.title,
        "event_title": event.title,
    }


def create_ticket_type_from_chat(user, data):
    if not user or not user.is_authenticated:
        return {"success": False, "error": "You must be logged in to create ticket types."}

    event_title = data.get("event_title", "").strip()
    if not event_title:
        return {"success": False, "error": "Please specify which event to add the ticket type to."}

    event = _find_event_by_title(user, event_title)
    if not event:
        return {
            "success": False,
            "error": f"Could not find an event matching \"{event_title}\". Please check the name.",
        }

    if not event.organization.user_can(user, "manage_tickets"):
        return {"success": False, "error": "You don't have permission to manage tickets for this event."}

    name = data.get("name", "").strip()
    if not name:
        return {"success": False, "error": "Ticket type name is required."}

    try:
        price = Decimal(str(data.get("price", 0)))
    except (InvalidOperation, ValueError):
        price = Decimal("0")

    ticket_type = TicketType.objects.create(
        event=event,
        name=name,
        description=data.get("description", ""),
        price=price,
        quantity=data.get("quantity", 100),
        max_per_order=data.get("max_per_order", 10),
        is_active=data.get("is_active", True),
    )

    return {
        "success": True,
        "url": f"/events/{event.organization.slug}/{event.slug}/edit/",
        "name": ticket_type.name,
        "event_title": event.title,
    }
