from django.urls import path
from apps.events import actions

app_name = 'events'

urlpatterns = [
    path('', actions.EventListView.as_view(), name='list'),
    path('discover/', actions.PublicEventListView.as_view(), name='discover'),
    path('organizer/<slug:org_slug>/', actions.PublicOrganizerView.as_view(), name='public_organizer'),
    path('create/', actions.EventCreateView.as_view(), name='create'),
    path('coupons/', actions.CouponListView.as_view(), name='coupons'),
    path('coupons/create/', actions.CouponCreateView.as_view(), name='coupon_create'),
    path('coupons/<int:coupon_id>/', actions.CouponDetailView.as_view(), name='coupon_detail'),
    path('coupons/<int:coupon_id>/toggle/', actions.CouponToggleView.as_view(), name='coupon_toggle'),
    path('coupons/<int:coupon_id>/delete/', actions.CouponDeleteView.as_view(), name='coupon_delete'),
    path('coupons/validate/', actions.ValidateCouponView.as_view(), name='validate_coupon'),
    path('<slug:org_slug>/<slug:event_slug>/', actions.PublicEventDetailView.as_view(), name='public_detail'),
    path('<slug:org_slug>/<slug:event_slug>/dashboard/', actions.EventDashboardView.as_view(), name='dashboard'),
    path('<slug:org_slug>/<slug:event_slug>/manage/', actions.EventDetailView.as_view(), name='detail'),
    path('<slug:org_slug>/<slug:event_slug>/tickets/', actions.TicketTypeManageView.as_view(), name='manage_ticket_types'),
    path('<slug:org_slug>/<slug:event_slug>/apply-feature/', actions.ApplyFeatureView.as_view(), name='apply_feature'),
    path('<slug:org_slug>/<slug:event_slug>/flyer/', actions.FlyerGeneratorView.as_view(), name='flyer_generator'),
    path('<slug:org_slug>/<slug:event_slug>/flyer/config/', actions.FlyerConfigView.as_view(), name='flyer_config'),
]