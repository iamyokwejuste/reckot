from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.timesince import timesince
from datetime import timedelta
from apps.events.models import Event
from apps.reports.models import ReportExport
from apps.reports.queries import get_event_summary
from apps.reports.services import generate_csv_export, generate_excel_export, generate_pdf_export, generate_json_export, get_recent_exports
from apps.tickets.models import Ticket, Booking
from apps.payments.models import Payment


class AnalyticsView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        now = timezone.now()

        user_events = Event.objects.filter(
            organization__members=user
        ).select_related('organization')

        total_revenue = Payment.objects.filter(
            booking__event__organization__members=user,
            status=Payment.Status.CONFIRMED
        ).aggregate(total=Sum('amount'))['total'] or 0

        tickets_sold = Ticket.objects.filter(
            booking__event__organization__members=user,
            booking__status=Booking.Status.CONFIRMED
        ).count()

        total_tickets = Ticket.objects.filter(
            booking__event__organization__members=user,
            booking__status=Booking.Status.CONFIRMED
        ).count()
        checked_in = Ticket.objects.filter(
            booking__event__organization__members=user,
            is_checked_in=True
        ).count()
        checkin_rate = (checked_in / total_tickets * 100) if total_tickets > 0 else 0

        active_events = user_events.filter(
            state=Event.State.PUBLISHED,
            end_at__gte=now
        ).count()

        upcoming_events = user_events.filter(
            state=Event.State.PUBLISHED,
            start_at__gte=now,
            start_at__lte=now + timedelta(days=7)
        ).order_by('start_at')[:4]

        recent_sales = Ticket.objects.filter(
            booking__event__organization__members=user,
            booking__status=Booking.Status.CONFIRMED
        ).select_related(
            'booking__user', 'ticket_type', 'booking__event'
        ).order_by('-booking__created_at')[:5]

        top_events = user_events.annotate(
            revenue=Sum('bookings__payment__amount', filter=Q(
                bookings__payment__status=Payment.Status.CONFIRMED
            )),
            ticket_count=Count('bookings__tickets', filter=Q(
                bookings__status=Booking.Status.CONFIRMED
            )),
            checkin_count=Count('bookings__tickets', filter=Q(
                bookings__tickets__is_checked_in=True
            ))
        ).order_by('-revenue')[:5]

        # All events for export modal
        all_events = user_events.order_by('-start_at')[:20]

        return render(request, 'reports/analytics.html', {
            'total_revenue': f"{total_revenue:,.0f}",
            'tickets_sold': f"{tickets_sold:,}",
            'checkin_rate': f"{checkin_rate:.1f}",
            'active_events': active_events,
            'upcoming_events': upcoming_events,
            'recent_sales': recent_sales,
            'top_events': top_events,
            'all_events': all_events,
        })


class ReportsDashboardView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        summary = get_event_summary(event.id)
        recent_exports = get_recent_exports(event.id)

        # Get pending payments count
        pending_count = Payment.objects.filter(
            booking__event=event,
            status=Payment.Status.PENDING
        ).count()
        summary['pending_count'] = pending_count

        # Sales timeline - last 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        sales_timeline = Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED,
            booking__created_at__gte=seven_days_ago
        ).annotate(
            date=TruncDate('booking__created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Fill in missing days
        timeline_dict = {item['date']: item['count'] for item in sales_timeline}
        sales_timeline_filled = []
        max_daily_sales = 0
        for i in range(7):
            date = (seven_days_ago + timedelta(days=i)).date()
            count = timeline_dict.get(date, 0)
            sales_timeline_filled.append({'date': date, 'count': count})
            if count > max_daily_sales:
                max_daily_sales = count

        # Revenue breakdown by ticket type
        revenue_breakdown = Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED
        ).values(
            'ticket_type__name',
            'ticket_type__price'
        ).annotate(
            sold=Count('id'),
            revenue=Sum('ticket_type__price')
        ).order_by('-revenue')

        revenue_breakdown_list = [
            {
                'name': item['ticket_type__name'],
                'price': item['ticket_type__price'],
                'sold': item['sold'],
                'revenue': item['revenue'] or 0
            }
            for item in revenue_breakdown
        ]
        summary['revenue_breakdown'] = revenue_breakdown_list

        # Ticket breakdown for initial load
        ticket_breakdown = Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED
        ).values('ticket_type__name').annotate(
            count=Count('id')
        ).order_by('-count')
        summary['ticket_breakdown'] = list(ticket_breakdown)

        # Recent activity
        recent_activity = self._get_recent_activity(event)

        return render(request, 'reports/dashboard.html', {
            'event': event,
            'summary': summary,
            'recent_exports': recent_exports,
            'report_types': ReportExport.Type.choices,
            'sales_timeline': sales_timeline_filled,
            'max_daily_sales': max_daily_sales,
            'recent_activity': recent_activity,
        })

    def _get_recent_activity(self, event, limit=5):
        activities = []
        now = timezone.now()

        # Recent ticket sales
        recent_tickets = Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED
        ).select_related(
            'booking__user', 'ticket_type'
        ).order_by('-booking__created_at')[:limit]

        for ticket in recent_tickets:
            email = ticket.booking.user.email if ticket.booking.user else 'Guest'
            activities.append({
                'type': 'sale',
                'title': 'New ticket sold',
                'description': f'{ticket.ticket_type.name} - {email}',
                'time': timesince(ticket.booking.created_at, now) + ' ago',
                'timestamp': ticket.booking.created_at
            })

        # Recent check-ins
        recent_checkins = Ticket.objects.filter(
            booking__event=event,
            is_checked_in=True,
            checked_in_at__isnull=False
        ).select_related(
            'booking__user', 'ticket_type'
        ).order_by('-checked_in_at')[:limit]

        for ticket in recent_checkins:
            email = ticket.booking.user.email if ticket.booking.user else 'Guest'
            activities.append({
                'type': 'checkin',
                'title': 'Attendee checked in',
                'description': f'{ticket.ticket_type.name} - {email}',
                'time': timesince(ticket.checked_in_at, now) + ' ago',
                'timestamp': ticket.checked_in_at
            })

        # Sort by timestamp and limit
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]


class RecentActivityView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        activities = self._get_recent_activity(event)
        return render(request, 'reports/_recent_activity.html', {
            'activities': activities,
        })

    def _get_recent_activity(self, event, limit=5):
        activities = []
        now = timezone.now()

        # Recent ticket sales
        recent_tickets = Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED
        ).select_related(
            'booking__user', 'ticket_type'
        ).order_by('-booking__created_at')[:limit]

        for ticket in recent_tickets:
            email = ticket.booking.user.email if ticket.booking.user else 'Guest'
            activities.append({
                'type': 'sale',
                'title': 'New ticket sold',
                'description': f'{ticket.ticket_type.name} - {email}',
                'time': timesince(ticket.booking.created_at, now) + ' ago',
                'timestamp': ticket.booking.created_at
            })

        # Recent check-ins
        recent_checkins = Ticket.objects.filter(
            booking__event=event,
            is_checked_in=True,
            checked_in_at__isnull=False
        ).select_related(
            'booking__user', 'ticket_type'
        ).order_by('-checked_in_at')[:limit]

        for ticket in recent_checkins:
            email = ticket.booking.user.email if ticket.booking.user else 'Guest'
            activities.append({
                'type': 'checkin',
                'title': 'Attendee checked in',
                'description': f'{ticket.ticket_type.name} - {email}',
                'time': timesince(ticket.checked_in_at, now) + ' ago',
                'timestamp': ticket.checked_in_at
            })

        # Sort by timestamp and limit
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]


class GenerateReportView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        report_type = request.POST.get('report_type')
        format_type = request.POST.get('format', 'CSV')
        mask_emails = request.POST.get('mask_emails', 'on') == 'on'
        if report_type not in dict(ReportExport.Type.choices):
            return render(request, 'reports/_error.html', {'error': 'Invalid report type'})
        try:
            if format_type == 'EXCEL':
                export = generate_excel_export(event, report_type, request.user, mask_emails)
            else:
                export = generate_csv_export(event, report_type, request.user, mask_emails)
            return render(request, 'reports/_export_ready.html', {'export': export})
        except Exception as e:
            return render(request, 'reports/_error.html', {'error': str(e)})


class DownloadReportView(LoginRequiredMixin, View):
    def get(self, request, export_ref):
        export = get_object_or_404(ReportExport, reference=export_ref)
        if not export.file:
            raise Http404('File not found')
        response = FileResponse(
            export.file.open('rb'),
            as_attachment=True,
            filename=export.file.name.split('/')[-1]
        )
        return response


class ReportsSummaryView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        summary = get_event_summary(event.id)
        return render(request, 'reports/_summary.html', {'summary': summary})


class LiveStatsView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)

        total_tickets = Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED
        ).count()

        checked_in = Ticket.objects.filter(
            booking__event=event,
            is_checked_in=True
        ).count()

        total_revenue = Payment.objects.filter(
            booking__event=event,
            status=Payment.Status.CONFIRMED
        ).aggregate(total=Sum('amount'))['total'] or 0

        pending_payments = Payment.objects.filter(
            booking__event=event,
            status=Payment.Status.PENDING
        ).count()

        ticket_breakdown = Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED
        ).values('ticket_type__name').annotate(
            count=Count('id')
        ).order_by('-count')

        return render(request, 'reports/_live_stats.html', {
            'event': event,
            'total_tickets': total_tickets,
            'checked_in': checked_in,
            'total_revenue': total_revenue,
            'pending_payments': pending_payments,
            'ticket_breakdown': ticket_breakdown,
            'check_in_rate': (checked_in / total_tickets * 100) if total_tickets > 0 else 0,
        })


class AttendeeListView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        print_mode = request.GET.get('print') == '1'

        tickets = Ticket.objects.filter(
            booking__event=event,
            booking__status=Booking.Status.CONFIRMED
        ).select_related(
            'booking__user',
            'ticket_type'
        ).order_by('booking__user__last_name', 'booking__user__first_name')

        return render(request, 'reports/attendee_list.html', {
            'event': event,
            'tickets': tickets,
            'print_mode': print_mode,
            'total_count': tickets.count(),
            'checked_in_count': tickets.filter(is_checked_in=True).count(),
        })


class ExportCenterView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        recent_exports = get_recent_exports(event.id)
        return render(request, 'reports/export_center.html', {
            'event': event,
            'recent_exports': recent_exports,
            'report_types': ReportExport.Type.choices,
        })


class ExportGenerateView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        from django.http import HttpResponseRedirect
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        report_type = request.POST.get('report_type')
        format_type = request.POST.get('format', 'PDF')
        mask_emails = request.POST.get('mask_emails', 'on') == 'on'

        if report_type not in dict(ReportExport.Type.choices):
            return render(request, 'reports/export_center.html', {
                'event': event,
                'error': 'Invalid report type',
                'recent_exports': get_recent_exports(event.id),
            })

        try:
            if format_type == 'PDF':
                export = generate_pdf_export(event, report_type, request.user, mask_emails)
            elif format_type == 'EXCEL':
                export = generate_excel_export(event, report_type, request.user, mask_emails)
            elif format_type == 'JSON':
                export = generate_json_export(event, report_type, request.user, mask_emails)
            else:
                export = generate_csv_export(event, report_type, request.user, mask_emails)

            return HttpResponseRedirect(f'/reports/download/{export.reference}/')
        except Exception as e:
            return render(request, 'reports/export_center.html', {
                'event': event,
                'error': str(e),
                'recent_exports': get_recent_exports(event.id),
            })
