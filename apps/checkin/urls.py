from django.urls import path
from apps.checkin import actions

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
