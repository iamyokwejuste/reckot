from django.urls import path
from apps.messaging import actions

app_name = 'messaging'

urlpatterns = [
    path('<slug:org_slug>/campaigns/', actions.CampaignListView.as_view(), name='campaign_list'),
    path('<slug:org_slug>/events/<slug:event_slug>/campaigns/new/', actions.CampaignCreateView.as_view(), name='campaign_create'),
    path('<slug:org_slug>/campaigns/<uuid:campaign_ref>/', actions.CampaignDetailView.as_view(), name='campaign_detail'),
    path('<slug:org_slug>/campaigns/<uuid:campaign_ref>/send/', actions.CampaignSendView.as_view(), name='campaign_send'),
    path('<slug:org_slug>/templates/', actions.TemplateListView.as_view(), name='template_list'),
    path('<slug:org_slug>/templates/new/', actions.TemplateCreateView.as_view(), name='template_create'),
    path('track/open/<uuid:tracking_id>/', actions.TrackOpenView.as_view(), name='track_open'),
    path('track/click/<uuid:tracking_id>/', actions.TrackClickView.as_view(), name='track_click'),
]
