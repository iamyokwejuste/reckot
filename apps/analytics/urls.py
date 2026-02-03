from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("revenue/", views.revenue_analytics, name="revenue"),
    path("events/", views.event_analytics, name="events"),
    path("tickets/", views.ticket_analytics, name="tickets"),
    path("payments/", views.payment_analytics, name="payments"),
]
