from django.urls import path
from apps.payments import actions

app_name = 'payments'

urlpatterns = [
    path('', actions.PaymentListView.as_view(), name='list'),
    path('checkout/', actions.CheckoutView.as_view(), name='checkout'),
    path(
        '<uuid:booking_ref>/select/',
        actions.PaymentSelectMethodView.as_view(),
        name='select'
    ),
    path(
        '<uuid:booking_ref>/start/',
        actions.PaymentStartView.as_view(),
        name='start'
    ),
    path(
        '<uuid:payment_ref>/poll/',
        actions.PaymentPollView.as_view(),
        name='poll'
    ),
    path(
        '<uuid:payment_ref>/success/',
        actions.PaymentSuccessView.as_view(),
        name='success'
    ),
    path(
        'webhook/',
        actions.PaymentWebhookView.as_view(),
        name='webhook'
    ),
    path(
        'webhook/campay/',
        actions.CampayWebhookView.as_view(),
        name='webhook_campay'
    ),
]
