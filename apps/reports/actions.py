import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.events.models import Event
from apps.payments.models import Payment
from apps.reports.queries import (
    get_event_summary,
    get_questions_summary,
)
from apps.reports.services import (
    generate_csv_export,
    generate_excel_export,
    generate_json_export,
    generate_pdf_export,
)
from apps.tickets.models import Booking, Ticket


class AnalyticsView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        now = timezone.now()

        user_events = Event.objects.filter(organization__members=user).select_related(
            "organization"
        )

        total_revenue = (
            Payment.objects.filter(
                booking__event__organization__members=user,
                status=Payment.Status.CONFIRMED,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        tickets_sold = Ticket.objects.filter(
            booking__event__organization__members=user,
            booking__status=Booking.Status.CONFIRMED,
        ).count()

        checked_in = Ticket.objects.filter(
            booking__event__organization__members=user,
            booking__status=Booking.Status.CONFIRMED,
            is_checked_in=True,
        ).count()
        checkin_rate = (checked_in / tickets_sold * 100) if tickets_sold > 0 else 0

        active_events = user_events.filter(
            state=Event.State.PUBLISHED, end_at__gte=now
        ).count()

        upcoming_events = user_events.filter(
            state=Event.State.PUBLISHED,
            start_at__gte=now,
            start_at__lte=now + timedelta(days=7),
        ).order_by("start_at")[:4]

        recent_sales = (
            Ticket.objects.filter(
                booking__event__organization__members=user,
                booking__status=Booking.Status.CONFIRMED,
            )
            .select_related("booking__user", "ticket_type", "booking__event")
            .order_by("-booking__created_at")[:5]
        )

        top_events = user_events.annotate(
            revenue=Sum(
                "bookings__payment__amount",
                filter=Q(bookings__payment__status=Payment.Status.CONFIRMED),
            ),
            ticket_count=Count(
                "bookings__tickets", filter=Q(bookings__status=Booking.Status.CONFIRMED)
            ),
            checkin_count=Count(
                "bookings__tickets", filter=Q(bookings__tickets__is_checked_in=True)
            ),
        ).order_by("-revenue")[:5]

        all_events = user_events.order_by("-start_at")[:20]

        # Convert to list to get accurate count after slicing
        upcoming_events_list = list(upcoming_events)

        analytics_metrics = json.dumps(
            {
                "total_revenue": float(total_revenue),
                "tickets_sold": tickets_sold,
                "check_in_rate": round(checkin_rate, 1),
                "total_checked_in": checked_in,
                "active_events": active_events,
                "upcoming_events_count": len(upcoming_events_list),
                "top_events_count": len(top_events),
            }
        )

        return render(
            request,
            "reports/analytics.html",
            {
                "total_revenue": f"{total_revenue:,.0f}",
                "tickets_sold": f"{tickets_sold:,}",
                "checkin_rate": f"{checkin_rate:.1f}",
                "active_events": active_events,
                "upcoming_events": upcoming_events_list,
                "recent_sales": recent_sales,
                "top_events": top_events,
                "all_events": all_events,
                "analytics_metrics": analytics_metrics,
                "now": now,
            },
        )


class ReportsDashboardView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        summary = get_event_summary(event.id)

        pending_count = Payment.objects.filter(
            booking__event=event, status=Payment.Status.PENDING
        ).count()
        summary["pending_count"] = pending_count

        seven_days_ago = timezone.now() - timedelta(days=7)
        sales_timeline = (
            Ticket.objects.filter(
                booking__event=event,
                booking__status=Booking.Status.CONFIRMED,
                booking__created_at__gte=seven_days_ago,
            )
            .annotate(date=TruncDate("booking__created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        timeline_dict = {item["date"]: item["count"] for item in sales_timeline}
        sales_timeline_filled = []
        max_daily_sales = 0
        for i in range(7):
            date = (seven_days_ago + timedelta(days=i)).date()
            count = timeline_dict.get(date, 0)
            sales_timeline_filled.append({"date": date, "count": count})
            if count > max_daily_sales:
                max_daily_sales = count

        revenue_breakdown = (
            Ticket.objects.filter(
                booking__event=event, booking__status=Booking.Status.CONFIRMED
            )
            .values("ticket_type__name", "ticket_type__price")
            .annotate(sold=Count("id"), revenue=Sum("ticket_type__price"))
            .order_by("-revenue")
        )

        revenue_breakdown_list = [
            {
                "name": item["ticket_type__name"],
                "price": item["ticket_type__price"],
                "sold": item["sold"],
                "revenue": item["revenue"] or 0,
            }
            for item in revenue_breakdown
        ]
        summary["revenue_breakdown"] = revenue_breakdown_list

        # Ticket breakdown for initial load
        ticket_breakdown = (
            Ticket.objects.filter(
                booking__event=event, booking__status=Booking.Status.CONFIRMED
            )
            .values("ticket_type__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        summary["ticket_breakdown"] = list(ticket_breakdown)

        recent_activity = self._get_recent_activity(event)

        event_metrics = json.dumps(
            {
                "event_title": event.title,
                "total_tickets": summary.get("total_tickets", 0),
                "checked_in": summary.get("checked_in", 0),
                "check_in_rate": summary.get("check_in_rate", 0),
                "total_revenue": float(summary.get("total_revenue", 0)),
                "pending_orders": pending_count,
                "ticket_types": len(revenue_breakdown_list),
                "days_until_event": (event.start_at.date() - timezone.now().date()).days
                if event.start_at
                else 0,
                "recent_sales_count": len(
                    [a for a in recent_activity if a["type"] == "sale"]
                ),
            }
        )

        return render(
            request,
            "reports/dashboard.html",
            {
                "event": event,
                "summary": summary,
                "sales_timeline": sales_timeline_filled,
                "max_daily_sales": max_daily_sales,
                "recent_activity": recent_activity,
                "event_metrics": event_metrics,
            },
        )

    def _get_recent_activity(self, event, limit=5):
        activities = []
        now = timezone.now()

        # Recent ticket sales
        recent_tickets = (
            Ticket.objects.filter(
                booking__event=event, booking__status=Booking.Status.CONFIRMED
            )
            .select_related("booking__user", "ticket_type")
            .order_by("-booking__created_at")[:limit]
        )

        for ticket in recent_tickets:
            email = ticket.booking.user.email if ticket.booking.user else "Guest"
            activities.append(
                {
                    "type": "sale",
                    "title": "New ticket sold",
                    "description": f"{ticket.ticket_type.name} - {email}",
                    "time": timesince(ticket.booking.created_at, now) + " ago",
                    "timestamp": ticket.booking.created_at,
                }
            )

        # Recent check-ins
        recent_checkins = (
            Ticket.objects.filter(
                booking__event=event, is_checked_in=True, checked_in_at__isnull=False
            )
            .select_related("booking__user", "ticket_type")
            .order_by("-checked_in_at")[:limit]
        )

        for ticket in recent_checkins:
            email = ticket.booking.user.email if ticket.booking.user else "Guest"
            activities.append(
                {
                    "type": "checkin",
                    "title": "Attendee checked in",
                    "description": f"{ticket.ticket_type.name} - {email}",
                    "time": timesince(ticket.checked_in_at, now) + " ago",
                    "timestamp": ticket.checked_in_at,
                }
            )

        # Sort by timestamp and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:limit]


class RecentActivityView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        activities = self._get_recent_activity(event)
        return render(
            request,
            "reports/_recent_activity.html",
            {
                "activities": activities,
            },
        )

    def _get_recent_activity(self, event, limit=5):
        activities = []
        now = timezone.now()

        # Recent ticket sales
        recent_tickets = (
            Ticket.objects.filter(
                booking__event=event, booking__status=Booking.Status.CONFIRMED
            )
            .select_related("booking__user", "ticket_type")
            .order_by("-booking__created_at")[:limit]
        )

        for ticket in recent_tickets:
            email = ticket.booking.user.email if ticket.booking.user else "Guest"
            activities.append(
                {
                    "type": "sale",
                    "title": "New ticket sold",
                    "description": f"{ticket.ticket_type.name} - {email}",
                    "time": timesince(ticket.booking.created_at, now) + " ago",
                    "timestamp": ticket.booking.created_at,
                }
            )

        recent_checkins = (
            Ticket.objects.filter(
                booking__event=event, is_checked_in=True, checked_in_at__isnull=False
            )
            .select_related("booking__user", "ticket_type")
            .order_by("-checked_in_at")[:limit]
        )

        for ticket in recent_checkins:
            email = ticket.booking.user.email if ticket.booking.user else "Guest"
            activities.append(
                {
                    "type": "checkin",
                    "title": "Attendee checked in",
                    "description": f"{ticket.ticket_type.name} - {email}",
                    "time": timesince(ticket.checked_in_at, now) + " ago",
                    "timestamp": ticket.checked_in_at,
                }
            )

        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:limit]


class GenerateReportView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        report_type = request.POST.get("report_type")
        format_type = request.POST.get("format", "CSV")
        mask_emails = request.POST.get("mask_emails", "on") == "on"
        if report_type not in dict(ReportExport.Type.choices):
            return render(
                request, "reports/_error.html", {"error": _("Invalid report type")}
            )
        try:
            if format_type == "EXCEL":
                export = generate_excel_export(
                    event, report_type, request.user, mask_emails
                )
            else:
                export = generate_csv_export(
                    event, report_type, request.user, mask_emails
                )
            return render(request, "reports/_export_ready.html", {"export": export})
        except Exception as e:
            return render(request, "reports/_error.html", {"error": str(e)})


class SalesTimelineView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        period = request.GET.get("period", "7d")

        if period == "30d":
            days = 30
        elif period == "all":
            days = 365
        else:
            days = 7

        start_date = timezone.now() - timedelta(days=days)

        sales_timeline = (
            Ticket.objects.filter(
                booking__event=event,
                booking__status=Booking.Status.CONFIRMED,
                booking__created_at__gte=start_date,
            )
            .annotate(date=TruncDate("booking__created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        timeline_dict = {item["date"]: item["count"] for item in sales_timeline}
        sales_timeline_filled = []
        max_daily_sales = 0

        for i in range(days):
            date = (start_date + timedelta(days=i)).date()
            count = timeline_dict.get(date, 0)
            sales_timeline_filled.append({"date": date, "count": count})
            if count > max_daily_sales:
                max_daily_sales = count

        return render(
            request,
            "reports/_sales_timeline.html",
            {
                "sales_timeline": sales_timeline_filled,
                "max_daily_sales": max_daily_sales,
            },
        )


class ReportsSummaryView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        summary = get_event_summary(event.id)
        return render(request, "reports/_summary.html", {"summary": summary})


class LiveStatsView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)

        total_tickets = Ticket.objects.filter(
            booking__event=event, booking__status=Booking.Status.CONFIRMED
        ).count()

        checked_in = Ticket.objects.filter(
            booking__event=event, is_checked_in=True
        ).count()

        total_revenue = (
            Payment.objects.filter(
                booking__event=event, status=Payment.Status.CONFIRMED
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        pending_payments = Payment.objects.filter(
            booking__event=event, status=Payment.Status.PENDING
        ).count()

        ticket_breakdown = (
            Ticket.objects.filter(
                booking__event=event, booking__status=Booking.Status.CONFIRMED
            )
            .values("ticket_type__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return render(
            request,
            "reports/_live_stats.html",
            {
                "event": event,
                "total_tickets": total_tickets,
                "checked_in": checked_in,
                "total_revenue": total_revenue,
                "pending_payments": pending_payments,
                "ticket_breakdown": ticket_breakdown,
                "check_in_rate": (checked_in / total_tickets * 100)
                if total_tickets > 0
                else 0,
            },
        )


class AttendeeListView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        from apps.events.models import CheckoutQuestion

        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        print_mode = request.GET.get("print") == "1"

        tickets = (
            Ticket.objects.filter(
                booking__event=event, booking__status=Booking.Status.CONFIRMED
            )
            .select_related("booking__user", "booking", "ticket_type")
            .prefetch_related("answers__question")
            .order_by("booking__user__last_name", "booking__user__first_name")
        )

        questions = CheckoutQuestion.objects.filter(event=event).order_by("order")

        return render(
            request,
            "reports/attendee_list.html",
            {
                "event": event,
                "tickets": tickets,
                "questions": questions,
                "print_mode": print_mode,
                "total_count": tickets.count(),
                "checked_in_count": tickets.filter(is_checked_in=True).count(),
            },
        )


class ExportCenterView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        return render(
            request,
            "reports/export_center.html",
            {
                "event": event,
            },
        )


class ExportGenerateView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        report_type = request.POST.get("report_type")
        format_type = request.POST.get("format", "PDF")
        mask_emails = request.POST.get("mask_emails", "on") == "on"

        valid_types = ['RSVP', 'PAYMENTS', 'CHECKINS', 'SWAG', 'FINANCIAL', 'TICKET_SALES']
        if report_type not in valid_types:
            messages.error(request, _("Invalid report type"))
            return redirect(
                "reports:export_center", org_slug=org_slug, event_slug=event_slug
            )

        try:
            if format_type == "PDF":
                content, filename, content_type = generate_pdf_export(
                    event, report_type, request.user, mask_emails
                )
            elif format_type == "EXCEL":
                content, filename, content_type = generate_excel_export(
                    event, report_type, request.user, mask_emails
                )
            elif format_type == "JSON":
                content, filename, content_type = generate_json_export(
                    event, report_type, request.user, mask_emails
                )
            else:
                content, filename, content_type = generate_csv_export(
                    event, report_type, request.user, mask_emails
                )

            response = HttpResponse(content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            messages.error(request, _("Export failed: %(error)s") % {"error": str(e)})
            return redirect(
                "reports:export_center", org_slug=org_slug, event_slug=event_slug
            )


class CustomResponsesView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related("organization"),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user,
        )
        questions_summary = get_questions_summary(event.id)
        return render(
            request,
            "reports/custom_responses.html",
            {
                "event": event,
                "questions_summary": questions_summary,
            },
        )
