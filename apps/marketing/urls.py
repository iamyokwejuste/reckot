from django.urls import path
from apps.marketing import actions

app_name = "marketing"

urlpatterns = [
    path(
        "ref/<str:code>/",
        actions.AffiliateRedirectView.as_view(),
        name="affiliate_redirect",
    ),
    path(
        "share/<slug:org_slug>/<slug:event_slug>/track/",
        actions.TrackShareView.as_view(),
        name="track_share",
    ),
    path(
        "share/<slug:org_slug>/<slug:event_slug>/urls/",
        actions.ShareUrlsView.as_view(),
        name="share_urls",
    ),
    path(
        "affiliates/<slug:org_slug>/",
        actions.AffiliateListView.as_view(),
        name="affiliate_list",
    ),
    path(
        "affiliates/<slug:org_slug>/create/",
        actions.AffiliateCreateView.as_view(),
        name="affiliate_create",
    ),
    path(
        "affiliates/<slug:org_slug>/<str:link_code>/",
        actions.AffiliateDetailView.as_view(),
        name="affiliate_detail",
    ),
]
