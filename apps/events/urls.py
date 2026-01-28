from django.urls import path
from . import actions

app_name = 'events'

urlpatterns = [
    path('', actions.EventListView.as_view(), name='list'),
    path('create/', actions.EventCreateView.as_view(), name='create'),
    path('<int:event_id>/', actions.EventDetailView.as_view(), name='detail'),
    path('<int:event_id>/manage-ticket-types/', actions.TicketTypeManageView.as_view(), name='manage_ticket_types'),
]