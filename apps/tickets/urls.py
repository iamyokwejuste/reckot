from django.urls import path
from apps.tickets import actions

app_name = "tickets"

urlpatterns = [
    path("", actions.TicketListView.as_view(), name="list"),
    path("my/", actions.MyTicketsView.as_view(), name="my_tickets"),
    path("lookup/", actions.TicketLookupView.as_view(), name="lookup"),
    path(
        "<str:ticket_code>/pdf/",
        actions.TicketPDFView.as_view(),
        name="ticket_pdf",
    ),
    path(
        "booking/<uuid:booking_ref>/pdf/",
        actions.BookingTicketsPDFView.as_view(),
        name="booking_pdf",
    ),
    path(
        "booking/<uuid:booking_ref>/download/",
        actions.PublicBookingPDFView.as_view(),
        name="public_booking_pdf",
    ),
]
