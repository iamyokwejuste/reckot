from django.urls import path
from . import actions

app_name = 'payments'

urlpatterns = [
    path(
        '<int:booking_id>/select/',
        actions.PaymentSelectMethodView.as_view(),
        name='select'
    ),
    path(
        '<int:booking_id>/start/',
        actions.PaymentStartView.as_view(),
        name='start'
    ),
    path(
        '<int:payment_id>/poll/',
        actions.PaymentPollView.as_view(),
        name='poll'
    ),
    path(
        '<int:payment_id>/success/',
        actions.PaymentSuccessView.as_view(),
        name='success'
    ),
    path(
        'webhook/',
        actions.PaymentWebhookView.as_view(),
        name='webhook'
    ),
]
