import uuid
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse, FileResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.events.forms import EventForm, TicketTypeForm
from apps.events.services import create_event
from apps.events.queries import get_user_events
from apps.events.models import (
    Event,
    Coupon,
    EventFlyerConfig,
    FlyerTextField,
    CheckoutQuestion,
    EventCustomization,
    FlyerGeneration,
    FlyerBilling,
)
from apps.events.flyer_service import generate_flyer
from apps.orgs.models import Organization, Membership, MemberRole
from apps.tickets.forms import BookingForm
from apps.tickets.services import create_booking
from apps.tickets.models import Ticket, TicketType, Booking
from apps.payments.models import Payment
from apps.payments.services import calculate_organization_balance
from decimal import Decimal


class PublicEventListView(View):
    def get(self, request):
        events = (
            Event.objects.filter(is_public=True, state=Event.State.PUBLISHED)
            .select_related("organization")
            .order_by("-start_at")
        )

        search = request.GET.get("q", "")
        if search:
            events = events.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(location__icontains=search)
            )

        location = request.GET.get("location", "")
        if location:
            events = events.filter(location__icontains=location)

        paginator = Paginator(events, 12)
        page = request.GET.get("page", 1)
        events = paginator.get_page(page)

        return render(
            request,
            "events/discover.html",
            {
                "events": events,
                "search": search,
                "location": location,
            },
        )


class PublicEventDetailView(View):
    def get(self, request, org_slug, event_slug):
        preview_token = request.GET.get("preview")

        if preview_token:
            event = get_object_or_404(
                Event.objects.select_related("organization"),
                organization__slug=org_slug,
                slug=event_slug,
                preview_token=preview_token,
            )
        else:
            event = get_object_or_404(
                Event.objects.select_related("organization"),
                organization__slug=org_slug,
                slug=event_slug,
                state=Event.State.PUBLISHED,
            )

        now = timezone.localtime(timezone.now())
        all_ticket_types = event.ticket_types.filter(is_active=True)

        available_tickets = []
        for tt in all_ticket_types:
            is_available = True
            status_message = None
            sales_started = False

            sales_start = (
                tt.sales_start.replace(tzinfo=None) if tt.sales_start else None
            )
            sales_end = tt.sales_end.replace(tzinfo=None) if tt.sales_end else None
            now_naive = now.replace(tzinfo=None)

            if sales_start and now_naive < sales_start:
                is_available = False
                if sales_start.date() == now_naive.date():
                    status_message = (
                        f"Sales start today at {sales_start.strftime('%I:%M %p')}"
                    )
                else:
                    status_message = (
                        f"Sales start {sales_start.strftime('%b %d, %Y at %I:%M %p')}"
                    )
            elif sales_end and now_naive > sales_end:
                is_available = False
                status_message = _("Sales ended")
            elif tt.available_quantity <= 0:
                is_available = False
                status_message = _("Sold out")
            else:
                if sales_start and now_naive >= sales_start:
                    sales_started = True

            tt.is_available = is_available
            tt.status_message = status_message
            tt.sales_started = sales_started
            available_tickets.append(tt)

        checkout_questions = event.checkout_questions.all()
        affiliate_code = request.session.get("affiliate_code")

        flyer_enabled = False
        try:
            flyer_config = event.flyer_config
            flyer_enabled = flyer_config.is_enabled and flyer_config.template_image
        except Exception:
            pass

        return render(
            request,
            "events/public_detail.html",
            {
                "event": event,
                "ticket_types": available_tickets,
                "checkout_questions": checkout_questions,
                "affiliate_code": affiliate_code,
                "flyer_enabled": flyer_enabled,
            },
        )


class PublicOrganizerView(View):
    def get(self, request, org_slug):
        organization = get_object_or_404(Organization, slug=org_slug)

        upcoming_events = Event.objects.filter(
            organization=organization,
            state=Event.State.PUBLISHED,
            is_public=True,
            start_at__gte=timezone.now(),
        ).order_by("start_at")

        past_events = Event.objects.filter(
            organization=organization,
            state=Event.State.PUBLISHED,
            is_public=True,
            start_at__lt=timezone.now(),
        ).order_by("-start_at")[:12]

        return render(
            request,
            "events/public_organizer.html",
            {
                "organization": organization,
                "upcoming_events": upcoming_events,
                "past_events": past_events,
            },
        )


class EventListView(LoginRequiredMixin, View):
    def get(self, request):
        events = get_user_events(request.user)
        return render(request, "events/list_events.html", {"events": events})


class EventCreateView(LoginRequiredMixin, View):
    def get(self, request):
        organizations = Organization.objects.filter(members=request.user)
        if not organizations.exists():
            return render(request, "events/no_org.html")
        form = EventForm()
        return render(
            request,
            "events/create_event.html",
            {
                "form": form,
                "organizations": organizations,
            },
        )

    def post(self, request):
        organizations = Organization.objects.filter(members=request.user)
        if not organizations.exists():
            return render(request, "events/no_org.html")

        org_id = request.POST.get("organization")
        organization = get_object_or_404(Organization, id=org_id, members=request.user)

        event, errors = create_event(
            request.user, organization, request.POST, request.FILES
        )
        if event:
            messages.success(
                request,
                _('Event "%(title)s" created successfully!') % {"title": event.title},
            )
            return redirect(
                "events:detail", org_slug=organization.slug, event_slug=event.slug
            )
        else:
            form = EventForm(request.POST, request.FILES)
            messages.error(
                request, _("Failed to create event. Please check the errors below.")
            )
            return render(
                request,
                "events/create_event.html",
                {"form": form, "organizations": organizations, "errors": errors},
            )


class TicketTypeManageView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        ticket_types = event.ticket_types.all()
        form = TicketTypeForm()
        return render(
            request,
            "events/manage_ticket_types.html",
            {"event": event, "ticket_types": ticket_types, "form": form},
        )

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        form = TicketTypeForm(request.POST)
        if form.is_valid():
            ticket_type = form.save(commit=False)
            ticket_type.event = event
            ticket_type.save()
            return redirect(
                "events:manage_ticket_types", org_slug=org_slug, event_slug=event_slug
            )
        ticket_types = event.ticket_types.all()
        return render(
            request,
            "events/manage_ticket_types.html",
            {"event": event, "ticket_types": ticket_types, "form": form},
        )


class TicketTypeEditView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug, ticket_type_id):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        ticket_type = get_object_or_404(TicketType, id=ticket_type_id, event=event)
        form = TicketTypeForm(instance=ticket_type)
        return render(
            request,
            "events/edit_ticket_type.html",
            {"event": event, "ticket_type": ticket_type, "form": form},
        )

    def post(self, request, org_slug, event_slug, ticket_type_id):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        ticket_type = get_object_or_404(TicketType, id=ticket_type_id, event=event)
        form = TicketTypeForm(request.POST, instance=ticket_type)
        if form.is_valid():
            form.save()
            return redirect(
                "events:manage_ticket_types", org_slug=org_slug, event_slug=event_slug
            )
        return render(
            request,
            "events/edit_ticket_type.html",
            {"event": event, "ticket_type": ticket_type, "form": form},
        )


class TicketTypeDeleteView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug, ticket_type_id):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        ticket_type = get_object_or_404(TicketType, id=ticket_type_id, event=event)
        if ticket_type.tickets.exists():
            return JsonResponse(
                {"error": _("Cannot delete ticket type with existing tickets")},
                status=400,
            )
        ticket_type.delete()
        return redirect(
            "events:manage_ticket_types", org_slug=org_slug, event_slug=event_slug
        )


class EventDetailView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        booking_form = BookingForm(initial={"ticket_type": event.ticket_types.first()})
        return render(
            request,
            "events/event_detail.html",
            {"event": event, "booking_form": booking_form},
        )

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        booking_form = BookingForm(request.POST)
        if booking_form.is_valid():
            ticket_type = booking_form.cleaned_data["ticket_type"]
            quantity = booking_form.cleaned_data["quantity"]
            booking, error = create_booking(request.user, ticket_type, quantity)
            if booking:
                return redirect("events:list")
            else:
                return render(
                    request,
                    "events/event_detail.html",
                    {"event": event, "booking_form": booking_form, "error": error},
                )
        return render(
            request,
            "events/event_detail.html",
            {"event": event, "booking_form": booking_form},
        )


class EventEditView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )
        form = EventForm(instance=event)
        return render(
            request,
            "events/edit_event.html",
            {
                "form": form,
                "event": event,
            },
        )

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect(
                "events:dashboard", org_slug=org_slug, event_slug=event.slug
            )

        return render(
            request,
            "events/edit_event.html",
            {
                "form": form,
                "event": event,
            },
        )


class EventDashboardView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        tickets = Ticket.objects.filter(booking__event=event)

        tickets_sold = tickets.count()
        checked_in = tickets.filter(is_checked_in=True).count()
        checkin_rate = (checked_in / tickets_sold * 100) if tickets_sold > 0 else 0

        revenue = (
            Payment.objects.filter(
                booking__event=event, status=Payment.Status.CONFIRMED
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        stats = {
            "tickets_sold": tickets_sold,
            "checked_in": checked_in,
            "checkin_rate": checkin_rate,
            "revenue": revenue,
        }

        public_url = reverse("events:public_detail", args=[org_slug, event_slug])
        preview_url = None
        if event.preview_token:
            preview_url = f"{public_url}?preview={event.preview_token}"

        return render(
            request,
            "events/event_dashboard.html",
            {
                "event": event,
                "stats": stats,
                "is_published": event.state == Event.State.PUBLISHED,
                "public_url": public_url,
                "preview_url": preview_url,
                "manage_tickets_url": reverse(
                    "events:manage_ticket_types", args=[org_slug, event_slug]
                ),
                "checkin_url": reverse(
                    "checkin:dashboard", args=[org_slug, event_slug]
                ),
                "export_url": reverse(
                    "reports:export_center", args=[org_slug, event_slug]
                ),
                "analytics_url": reverse(
                    "reports:dashboard", args=[org_slug, event_slug]
                ),
                "flyer_config_url": reverse(
                    "events:flyer_config", args=[org_slug, event_slug]
                ),
                "edit_event_url": reverse("events:edit", args=[org_slug, event_slug]),
            },
        )


class ApplyFeatureView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event,
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        if not event.is_public:
            return redirect(
                "events:dashboard", org_slug=org_slug, event_slug=event_slug
            )

        if event.is_featured:
            return redirect(
                "events:dashboard", org_slug=org_slug, event_slug=event_slug
            )

        event.feature_requested_at = timezone.now()
        event.feature_rejection_reason = ""
        event.save(update_fields=["feature_requested_at", "feature_rejection_reason"])

        return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)


class TogglePublishView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event,
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        if event.state == Event.State.PUBLISHED:
            event.state = Event.State.DRAFT
        else:
            event.state = Event.State.PUBLISHED

        event.save(update_fields=["state"])
        return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)


class TogglePublicView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event,
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        event.is_public = not event.is_public
        event.save(update_fields=["is_public"])
        return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)


class GeneratePreviewTokenView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event,
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )
        event.generate_preview_token()
        return redirect("events:dashboard", org_slug=org_slug, event_slug=event_slug)


class CouponListView(LoginRequiredMixin, View):
    def get(self, request):
        coupons = (
            Coupon.objects.filter(organization__members=request.user)
            .select_related("organization", "event")
            .annotate(usage_count=Count("usages"))
            .order_by("-created_at")
        )

        stats = {
            "total": coupons.count(),
            "active": coupons.filter(is_active=True).count(),
        }

        return render(
            request,
            "events/coupons/list.html",
            {
                "coupons": coupons,
                "stats": stats,
            },
        )


class CouponCreateView(LoginRequiredMixin, View):
    def get(self, request):
        organizations = Organization.objects.filter(members=request.user)
        events = Event.objects.filter(organization__members=request.user)
        return render(
            request,
            "events/coupons/create.html",
            {
                "organizations": organizations,
                "events": events,
            },
        )

    def post(self, request):
        org_id = request.POST.get("organization")
        organization = get_object_or_404(Organization, id=org_id, members=request.user)

        event_id = request.POST.get("event")
        event = None
        if event_id:
            event = get_object_or_404(Event, id=event_id, organization=organization)

        code = request.POST.get("code", "").strip().upper()
        if not code:
            code = uuid.uuid4().hex[:8].upper()

        existing = Coupon.objects.filter(organization=organization, code=code).exists()
        if existing:
            organizations = Organization.objects.filter(members=request.user)
            events = Event.objects.filter(organization__members=request.user)
            return render(
                request,
                "events/coupons/create.html",
                {
                    "organizations": organizations,
                    "events": events,
                    "error": _(
                        "A coupon with this code already exists in this organization."
                    ),
                },
            )

        discount_type = request.POST.get("discount_type", "PERCENTAGE")
        discount_value = request.POST.get("discount_value", 0)
        assignment_type = request.POST.get("assignment_type", "PUBLIC")
        assigned_email = request.POST.get("assigned_email", "").strip()
        assigned_emails_raw = request.POST.get("assigned_emails", "").strip()
        assigned_emails = (
            [e.strip() for e in assigned_emails_raw.split(",") if e.strip()]
            if assigned_emails_raw
            else []
        )
        max_uses = request.POST.get("max_uses", 1)
        description = request.POST.get("description", "").strip()
        valid_from = request.POST.get("valid_from") or None
        valid_until = request.POST.get("valid_until") or None

        Coupon.objects.create(
            organization=organization,
            event=event,
            code=code,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            assignment_type=assignment_type,
            assigned_email=assigned_email,
            assigned_emails=assigned_emails,
            max_uses=int(max_uses) if max_uses else 1,
            valid_from=valid_from,
            valid_until=valid_until,
            is_active=True,
            created_by=request.user,
        )

        return redirect("events:coupons")


class CouponDetailView(LoginRequiredMixin, View):
    def get(self, request, coupon_id):
        coupon = get_object_or_404(
            Coupon.objects.select_related("organization", "event"),
            id=coupon_id,
            organization__members=request.user,
        )
        usages = coupon.usages.select_related("booking__user").order_by("-used_at")[:50]
        return render(
            request,
            "events/coupons/detail.html",
            {
                "coupon": coupon,
                "usages": usages,
            },
        )


class CouponToggleView(LoginRequiredMixin, View):
    def post(self, request, coupon_id):
        coupon = get_object_or_404(
            Coupon, id=coupon_id, organization__members=request.user
        )
        coupon.is_active = not coupon.is_active
        coupon.save(update_fields=["is_active"])
        return redirect("events:coupon_detail", coupon_id=coupon.id)


class CouponDeleteView(LoginRequiredMixin, View):
    def post(self, request, coupon_id):
        coupon = get_object_or_404(
            Coupon, id=coupon_id, organization__members=request.user
        )
        coupon.delete()
        return redirect("events:coupons")


class ValidateCouponView(View):
    def post(self, request):
        code = request.POST.get("code", "").strip().upper()
        event_id = request.POST.get("event_id")
        email = request.POST.get("email", "").strip()

        if not code:
            return JsonResponse(
                {"valid": False, "error": _("Please enter a coupon code")}
            )

        coupon = Coupon.objects.filter(
            Q(code=code), Q(event_id=event_id) | Q(event__isnull=True)
        ).first()

        if not coupon:
            return JsonResponse({"valid": False, "error": _("Invalid coupon code")})

        if not coupon.is_valid:
            return JsonResponse(
                {"valid": False, "error": _("This coupon is no longer valid")}
            )

        if email and not coupon.can_be_used_by(email):
            return JsonResponse(
                {
                    "valid": False,
                    "error": _("This coupon cannot be used with your email"),
                }
            )

        return JsonResponse(
            {
                "valid": True,
                "discount_type": coupon.discount_type,
                "discount_value": float(coupon.discount_value),
                "code": coupon.code,
            }
        )


FLYER_PAY_PER_USE_PRICE = 25


class FlyerTicketVerificationView(View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            state=Event.State.PUBLISHED,
        )

        ticket_verification = request.POST.get("ticket_verification", "").strip()

        if not ticket_verification:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Please provide your email, phone number, or ticket code.",
                },
                status=400,
            )

        is_email = "@" in ticket_verification
        is_phone = ticket_verification.startswith("+") or ticket_verification.isdigit()

        if is_email:
            if FlyerGeneration.objects.filter(event=event, email__iexact=ticket_verification).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "error": "You have already generated a flyer with this email. Each person can only generate one flyer per event.",
                    },
                    status=403,
                )

            matching_tickets = Ticket.objects.filter(
                Q(attendee_email__iexact=ticket_verification) |
                Q(booking__user__email__iexact=ticket_verification, attendee_email="") |
                Q(booking__guest_email__iexact=ticket_verification, attendee_email=""),
                booking__event=event,
                booking__status=Booking.Status.CONFIRMED
            ).select_related("booking__user").first()

        elif is_phone:
            if FlyerGeneration.objects.filter(event=event, phone=ticket_verification).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "error": "You have already generated a flyer with this phone number. Each person can only generate one flyer per event.",
                    },
                    status=403,
                )

            matching_tickets = Ticket.objects.filter(
                Q(booking__user__phone_number=ticket_verification) |
                Q(booking__guest_phone=ticket_verification),
                booking__event=event,
                booking__status=Booking.Status.CONFIRMED
            ).select_related("booking__user").first()

        else:
            matching_tickets = Ticket.objects.filter(
                code__iexact=ticket_verification,
                booking__event=event,
                booking__status=Booking.Status.CONFIRMED
            ).select_related("booking__user").first()

            if matching_tickets:
                ticket_email = matching_tickets.attendee_email or matching_tickets.booking.buyer_email
                ticket_phone = matching_tickets.booking.user.phone_number if matching_tickets.booking.user else matching_tickets.booking.guest_phone

                if ticket_email and FlyerGeneration.objects.filter(event=event, email__iexact=ticket_email).exists():
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "A flyer has already been generated for this ticket's attendee.",
                        },
                        status=403,
                    )
                if ticket_phone and FlyerGeneration.objects.filter(event=event, phone=ticket_phone).exists():
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "A flyer has already been generated for this ticket's attendee.",
                        },
                        status=403,
                    )

        if not matching_tickets:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No valid ticket found. Please check your information and try again.",
                },
                status=403,
            )

        verified_ticket = matching_tickets

        return JsonResponse(
            {
                "success": True,
                "ticket_code": str(verified_ticket.code),
            }
        )


class FlyerGeneratorView(View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            state=Event.State.PUBLISHED,
        )

        has_feature = event.organization.has_feature("flyer_generator")
        has_paid_tickets = TicketType.objects.filter(event=event, price__gt=0).exists()
        flyer_free = has_feature or has_paid_tickets

        try:
            config = event.flyer_config
            if not config.is_enabled:
                return render(request, "events/flyer_disabled.html", {"event": event})
            if not flyer_free and not config.pay_per_use_accepted:
                return render(request, "events/flyer_upgrade.html", {"event": event})
        except EventFlyerConfig.DoesNotExist:
            return render(request, "events/flyer_disabled.html", {"event": event})

        text_fields = config.text_fields.all()

        return render(
            request,
            "events/flyer_generator.html",
            {
                "event": event,
                "config": config,
                "text_fields": text_fields,
                "has_feature": flyer_free,
                "pay_per_use_price": FLYER_PAY_PER_USE_PRICE,
            },
        )

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            state=Event.State.PUBLISHED,
        )

        has_feature = event.organization.has_feature("flyer_generator")
        has_paid_tickets = TicketType.objects.filter(event=event, price__gt=0).exists()
        flyer_free = has_feature or has_paid_tickets

        try:
            config = event.flyer_config
            if not config.is_enabled:
                return HttpResponse(_("Flyer generation not enabled"), status=403)
        except EventFlyerConfig.DoesNotExist:
            return HttpResponse(_("Flyer not configured"), status=404)

        ticket_verification = request.POST.get("ticket_verification", "").strip()

        if not ticket_verification:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Please provide your email, phone number, or ticket code to verify your ticket.",
                },
                status=400,
            )

        is_email = "@" in ticket_verification
        is_phone = ticket_verification.startswith("+") or ticket_verification.isdigit()
        attendee_email = ""
        attendee_phone = ""

        if is_email:
            if FlyerGeneration.objects.filter(event=event, email__iexact=ticket_verification).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "error": "You have already generated a flyer with this email.",
                    },
                    status=403,
                )
            attendee_email = ticket_verification

            verified_ticket = Ticket.objects.filter(
                Q(attendee_email__iexact=ticket_verification) |
                Q(booking__user__email__iexact=ticket_verification, attendee_email="") |
                Q(booking__guest_email__iexact=ticket_verification, attendee_email=""),
                booking__event=event,
                booking__status=Booking.Status.CONFIRMED
            ).select_related("booking__user").first()

        elif is_phone:
            if FlyerGeneration.objects.filter(event=event, phone=ticket_verification).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "error": "You have already generated a flyer with this phone number.",
                    },
                    status=403,
                )
            attendee_phone = ticket_verification

            verified_ticket = Ticket.objects.filter(
                Q(booking__user__phone_number=ticket_verification) |
                Q(booking__guest_phone=ticket_verification),
                booking__event=event,
                booking__status=Booking.Status.CONFIRMED
            ).select_related("booking__user").first()

        else:
            verified_ticket = Ticket.objects.filter(
                code__iexact=ticket_verification,
                booking__event=event,
                booking__status=Booking.Status.CONFIRMED
            ).select_related("booking__user").first()

            if verified_ticket:
                ticket_email = verified_ticket.attendee_email or verified_ticket.booking.buyer_email
                ticket_phone = verified_ticket.booking.user.phone_number if verified_ticket.booking.user else verified_ticket.booking.guest_phone

                if ticket_email and FlyerGeneration.objects.filter(event=event, email__iexact=ticket_email).exists():
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "A flyer has already been generated for this ticket's attendee.",
                        },
                        status=403,
                    )
                if ticket_phone and FlyerGeneration.objects.filter(event=event, phone=ticket_phone).exists():
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "A flyer has already been generated for this ticket's attendee.",
                        },
                        status=403,
                    )

                attendee_email = ticket_email
                attendee_phone = ticket_phone or ""

        if not verified_ticket:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No valid ticket found. Please check your information and try again.",
                },
                status=403,
            )

        if not flyer_free and config.pay_per_use_accepted:
            balance_data = calculate_organization_balance(event.organization.id)
            available_balance = balance_data["available_balance"]

            if available_balance < Decimal(str(FLYER_PAY_PER_USE_PRICE)):
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Insufficient balance to generate flyer. Required: {FLYER_PAY_PER_USE_PRICE} FCFA, Available: {available_balance} FCFA. Please contact the event organizer.",
                    },
                    status=403,
                )

        user_photo = request.FILES.get("photo")
        text_values = {}
        for key, value in request.POST.items():
            if key.startswith("field_"):
                field_id = key.replace("field_", "")
                text_values[field_id] = value

        try:
            flyer_image = generate_flyer(config, user_photo, text_values)

            if not flyer_free and config.pay_per_use_accepted:
                FlyerGeneration.objects.create(
                    event=event,
                    ticket=verified_ticket,
                    email=attendee_email,
                    phone=attendee_phone,
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                )
                billing, _created = FlyerBilling.objects.get_or_create(
                    event=event, defaults={"rate_per_flyer": FLYER_PAY_PER_USE_PRICE}
                )
                billing.update_totals()
            else:
                FlyerGeneration.objects.create(
                    event=event,
                    ticket=verified_ticket,
                    email=attendee_email,
                    phone=attendee_phone,
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                )

            response = FileResponse(flyer_image, content_type="image/jpeg")
            response["Content-Disposition"] = (
                f'inline; filename="{event.slug}-flyer.jpg"'
            )
            return response
        except Exception as e:
            return HttpResponse(f"Error generating flyer: {str(e)}", status=500)


class FlyerConfigView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        membership = Membership.objects.filter(
            organization=event.organization, user=request.user
        ).first()

        is_organizer = membership and membership.role in [
            MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MANAGER
        ]

        has_feature = event.organization.has_feature("flyer_generator")
        has_paid_tickets = TicketType.objects.filter(event=event, price__gt=0).exists()
        flyer_free = has_feature or has_paid_tickets

        try:
            config = event.flyer_config
        except EventFlyerConfig.DoesNotExist:
            config = None

        return render(
            request,
            "events/flyer_config.html",
            {
                "event": event,
                "config": config,
                "has_feature": flyer_free,
                "has_paid_tickets": has_paid_tickets,
                "current_plan": event.organization.current_plan,
                "is_organizer": is_organizer,
            },
        )

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        membership = Membership.objects.filter(
            organization=event.organization, user=request.user
        ).first()

        is_organizer = membership and membership.role in [
            MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MANAGER
        ]

        try:
            config = event.flyer_config
        except EventFlyerConfig.DoesNotExist:
            config = EventFlyerConfig(event=event)

        config.is_enabled = request.POST.get("is_enabled") == "on"

        if "template_image" in request.FILES:
            config.template_image = request.FILES["template_image"]

        config.photo_x = int(request.POST.get("photo_x") or 50)
        config.photo_y = int(request.POST.get("photo_y") or 50)
        config.photo_width = int(request.POST.get("photo_width") or 200)
        config.photo_height = int(request.POST.get("photo_height") or 200)
        config.photo_shape = request.POST.get("photo_shape") or "CIRCLE"
        config.photo_border_width = int(request.POST.get("photo_border_width") or 0)
        config.photo_border_color = request.POST.get("photo_border_color") or "#ffffff"
        photo_bg = request.POST.get("photo_bg_color") or "rgba(0,0,0,0)"
        config.photo_bg_color = "rgba(0,0,0,0)" if photo_bg == "transparent" else photo_bg
        config.output_width = int(request.POST.get("output_width") or 1080)
        config.output_height = int(request.POST.get("output_height") or 1080)

        if (
            request.POST.get("accept_pay_per_use") == "1"
            and not config.pay_per_use_accepted
        ):
            if not is_organizer:
                messages.error(request, "Only organizers can accept pay-per-use terms")
                return redirect("events:flyer_config", org_slug=org_slug, event_slug=event_slug)
            config.pay_per_use_accepted = True
            config.pay_per_use_accepted_at = timezone.now()

        if "template_image" in request.FILES:
            if config.pay_per_use_accepted and config.template_change_count > 0:
                billing, _created = FlyerBilling.objects.get_or_create(
                    event=event, defaults={"rate_per_flyer": FLYER_PAY_PER_USE_PRICE}
                )
                billing.total_amount += 1000
                billing.save(update_fields=["total_amount", "updated_at"])
            config.template_change_count += 1

        try:
            config.save()
        except Exception as e:
            messages.error(request, f"Failed to save configuration: {str(e)}")
            return redirect("events:flyer_config", org_slug=org_slug, event_slug=event_slug)

        config.text_fields.all().delete()

        fields_json = request.POST.get("fields_json", "[]")
        try:
            fields = json.loads(fields_json)
        except json.JSONDecodeError:
            fields = []

        for i, field in enumerate(fields):
            if not field.get("label", "").strip():
                continue
            field_bg = field.get("bg_color", "rgba(0,0,0,0.3)")
            if field_bg == "transparent":
                field_bg = "rgba(0,0,0,0)"
            FlyerTextField.objects.create(
                flyer_config=config,
                label=field.get("label", ""),
                placeholder=field.get("placeholder", ""),
                is_required=field.get("required", True),
                order=i,
                x=int(field.get("x", 0)),
                y=int(field.get("y", 0)),
                max_width=int(field.get("max_width", 400)),
                font_size=int(field.get("font_size", 32)),
                font_color=field.get("font_color", "#ffffff"),
                text_align=field.get("text_align", "CENTER"),
                bg_color=field_bg,
            )

        messages.success(request, "Flyer configuration saved successfully")
        return redirect("events:flyer_config", org_slug=org_slug, event_slug=event_slug)


class CheckoutQuestionsView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )
        questions = event.checkout_questions.all()
        return render(
            request,
            "events/checkout_questions.html",
            {
                "event": event,
                "questions": questions,
            },
        )

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event,
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        action = request.POST.get("action")

        if action == "add":
            CheckoutQuestion.objects.create(
                event=event,
                question=request.POST.get("question"),
                field_type=request.POST.get("field_type", "TEXT"),
                options=[
                    o.strip()
                    for o in request.POST.get("options", "").split("\n")
                    if o.strip()
                ],
                is_required=request.POST.get("is_required") == "on",
                per_ticket=request.POST.get("per_ticket") == "on",
                order=event.checkout_questions.count(),
            )
        elif action == "delete":
            question_id = request.POST.get("question_id")
            CheckoutQuestion.objects.filter(id=question_id, event=event).delete()
        elif action == "reorder":
            import json

            order_data = json.loads(request.POST.get("order", "[]"))
            for i, qid in enumerate(order_data):
                CheckoutQuestion.objects.filter(id=qid, event=event).update(order=i)

        return redirect(
            "events:checkout_questions", org_slug=org_slug, event_slug=event_slug
        )


class EventCustomizationView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )
        try:
            customization = event.customization
        except EventCustomization.DoesNotExist:
            customization = None

        return render(
            request,
            "events/customization.html",
            {
                "event": event,
                "customization": customization,
            },
        )

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event,
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )

        try:
            customization = event.customization
        except EventCustomization.DoesNotExist:
            customization = EventCustomization(event=event)

        customization.primary_color = request.POST.get("primary_color", "#000000")
        customization.secondary_color = request.POST.get("secondary_color", "#ffffff")
        customization.background_color = request.POST.get("background_color", "#ffffff")
        customization.text_color = request.POST.get("text_color", "#000000")
        customization.heading_font = request.POST.get("heading_font", "system-ui")
        customization.body_font = request.POST.get("body_font", "system-ui")
        customization.layout_template = request.POST.get("layout_template", "DEFAULT")
        customization.hide_reckot_branding = (
            request.POST.get("hide_reckot_branding") == "on"
        )

        if "hero_image" in request.FILES:
            customization.hero_image = request.FILES["hero_image"]
        if "logo" in request.FILES:
            customization.logo = request.FILES["logo"]

        customization.save()
        return redirect(
            "events:customization", org_slug=org_slug, event_slug=event_slug
        )
