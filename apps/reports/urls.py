from django.urls import path
from . import actions

app_name = 'reports'

urlpatterns = [
    path(
        '',
        actions.AnalyticsView.as_view(),
        name='analytics'
    ),
    path(
        '<int:event_id>/',
        actions.ReportsDashboardView.as_view(),
        name='dashboard'
    ),
    path(
        '<int:event_id>/generate/',
        actions.GenerateReportView.as_view(),
        name='generate'
    ),
    path(
        '<int:event_id>/summary/',
        actions.ReportsSummaryView.as_view(),
        name='summary'
    ),
    path(
        'download/<int:export_id>/',
        actions.DownloadReportView.as_view(),
        name='download'
    ),
]
