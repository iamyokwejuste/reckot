from django.urls import path
from apps.reports import actions

app_name = 'reports'

urlpatterns = [
    path('', actions.AnalyticsView.as_view(), name='analytics'),
    path('<slug:org_slug>/<slug:event_slug>/', actions.ReportsDashboardView.as_view(), name='dashboard'),
    path('<slug:org_slug>/<slug:event_slug>/generate/', actions.GenerateReportView.as_view(), name='generate'),
    path('<slug:org_slug>/<slug:event_slug>/summary/', actions.ReportsSummaryView.as_view(), name='summary'),
    path('<slug:org_slug>/<slug:event_slug>/live-stats/', actions.LiveStatsView.as_view(), name='live_stats'),
    path('<slug:org_slug>/<slug:event_slug>/attendees/', actions.AttendeeListView.as_view(), name='attendee_list'),
    path('<slug:org_slug>/<slug:event_slug>/export/', actions.ExportCenterView.as_view(), name='export_center'),
    path('<slug:org_slug>/<slug:event_slug>/export/generate/', actions.ExportGenerateView.as_view(), name='export_generate'),
    path('download/<uuid:export_ref>/', actions.DownloadReportView.as_view(), name='download'),
]
