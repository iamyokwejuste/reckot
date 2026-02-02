from django.urls import path
from apps.checkin import actions, api

app_name = "checkin"

urlpatterns = [
    path("", actions.CheckInListView.as_view(), name="list"),
    path("ticket/<str:code>/", actions.CheckInTicketView.as_view(), name="ticket"),
    path(
        "swag/<uuid:checkin_ref>/<int:item_id>/",
        actions.CollectSwagView.as_view(),
        name="collect_swag",
    ),
    path(
        "<slug:org_slug>/<slug:event_slug>/",
        actions.CheckInDashboardView.as_view(),
        name="dashboard",
    ),
    path(
        "<slug:org_slug>/<slug:event_slug>/verify/",
        actions.CheckInVerifyView.as_view(),
        name="verify",
    ),
    path(
        "<slug:org_slug>/<slug:event_slug>/search/",
        actions.CheckInSearchView.as_view(),
        name="search",
    ),
    path(
        "<slug:org_slug>/<slug:event_slug>/stats/",
        actions.CheckInStatsView.as_view(),
        name="stats",
    ),
]

api_urlpatterns = [
    path(
        "api/checkin/<slug:org_slug>/<slug:event_slug>/offline-data/",
        api.OfflineDataView.as_view(),
        name="offline_data",
    ),
    path("api/checkin/sync/", api.SyncCheckinView.as_view(), name="sync_checkin"),
    path(
        "api/checkin/swag/sync/",
        api.SyncSwagCollectionView.as_view(),
        name="sync_swag",
    ),
]

urlpatterns += api_urlpatterns
