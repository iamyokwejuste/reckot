from django.urls import path
from . import actions

app_name = 'checkin'

urlpatterns = [
    path(
        '<int:event_id>/',
        actions.CheckInDashboardView.as_view(),
        name='dashboard'
    ),
    path(
        '<int:event_id>/verify/',
        actions.CheckInVerifyView.as_view(),
        name='verify'
    ),
    path(
        '<int:event_id>/search/',
        actions.CheckInSearchView.as_view(),
        name='search'
    ),
    path(
        '<int:event_id>/stats/',
        actions.CheckInStatsView.as_view(),
        name='stats'
    ),
    path(
        'ticket/<uuid:code>/',
        actions.CheckInTicketView.as_view(),
        name='ticket'
    ),
    path(
        '<int:checkin_id>/swag/<int:item_id>/',
        actions.CollectSwagView.as_view(),
        name='collect_swag'
    ),
]
