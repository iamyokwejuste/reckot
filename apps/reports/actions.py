from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from apps.events.models import Event
from .models import ReportExport
from .queries import get_event_summary
from .services import generate_csv_export, generate_excel_export, get_recent_exports


class AnalyticsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'reports/analytics.html', {})


class ReportsDashboardView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        summary = get_event_summary(event_id)
        recent_exports = get_recent_exports(event_id)
        return render(request, 'reports/dashboard.html', {
            'event': event,
            'summary': summary,
            'recent_exports': recent_exports,
            'report_types': ReportExport.Type.choices,
        })


class GenerateReportView(LoginRequiredMixin, View):
    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        report_type = request.POST.get('report_type')
        format_type = request.POST.get('format', 'CSV')
        mask_emails = request.POST.get('mask_emails', 'on') == 'on'
        if report_type not in dict(ReportExport.Type.choices):
            return render(request, 'reports/_error.html', {
                'error': 'Invalid report type'
            })
        try:
            if format_type == 'EXCEL':
                export = generate_excel_export(event, report_type, request.user, mask_emails)
            else:
                export = generate_csv_export(event, report_type, request.user, mask_emails)
            return render(request, 'reports/_export_ready.html', {'export': export})
        except Exception as e:
            return render(request, 'reports/_error.html', {'error': str(e)})


class DownloadReportView(LoginRequiredMixin, View):
    def get(self, request, export_id):
        export = get_object_or_404(ReportExport, pk=export_id)
        if not export.file:
            raise Http404('File not found')
        response = FileResponse(
            export.file.open('rb'),
            as_attachment=True,
            filename=export.file.name.split('/')[-1]
        )
        return response


class ReportsSummaryView(LoginRequiredMixin, View):
    def get(self, request, event_id):
        summary = get_event_summary(event_id)
        return render(request, 'reports/_summary.html', {'summary': summary})
