from django.urls import path
from apps.tickets import actions

app_name = 'tickets'

urlpatterns = [
    path('', actions.TicketListView.as_view(), name='list'),
    path('my/', actions.MyTicketsView.as_view(), name='my_tickets'),
    path('<uuid:ticket_code>/pdf/', actions.TicketPDFView.as_view(), name='ticket_pdf'),
    path('booking/<uuid:booking_ref>/pdf/', actions.BookingTicketsPDFView.as_view(), name='booking_pdf'),
]
