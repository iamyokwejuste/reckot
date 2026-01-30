from django.urls import path
from apps.payments import actions

app_name = "payments"

urlpatterns = [
    path("", actions.PaymentListView.as_view(), name="list"),
    path("checkout/", actions.CheckoutView.as_view(), name="checkout"),
    path(
        "<uuid:booking_ref>/select/",
        actions.PaymentSelectMethodView.as_view(),
        name="select",
    ),
    path("<uuid:booking_ref>/start/", actions.PaymentStartView.as_view(), name="start"),
    path("<uuid:payment_ref>/poll/", actions.PaymentPollView.as_view(), name="poll"),
    path(
        "<uuid:payment_ref>/success/",
        actions.PaymentSuccessView.as_view(),
        name="success",
    ),
    path("webhook/", actions.PaymentWebhookView.as_view(), name="webhook"),
    path("webhook/campay/", actions.CampayWebhookView.as_view(), name="webhook_campay"),
    path(
        "<uuid:payment_ref>/invoice/",
        actions.InvoiceDownloadView.as_view(),
        name="invoice",
    ),
    path(
        "<uuid:payment_ref>/refund/",
        actions.RefundRequestView.as_view(),
        name="refund_request",
    ),
    path("refunds/", actions.RefundListView.as_view(), name="refunds"),
    path(
        "refunds/<int:refund_id>/process/",
        actions.RefundProcessView.as_view(),
        name="refund_process",
    ),
    path("track/<uuid:token>/", actions.TransactionStatusView.as_view(), name="track"),
    path("transactions/", actions.TransactionHistoryView.as_view(), name="transactions"),
    path("withdrawals/", actions.WithdrawalListView.as_view(), name="withdrawals"),
    path(
        "withdrawals/balance/",
        actions.WithdrawalBalanceView.as_view(),
        name="withdrawal_balance",
    ),
    path(
        "withdrawals/request/",
        actions.WithdrawalRequestView.as_view(),
        name="withdrawal_request",
    ),
]
