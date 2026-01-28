from django.urls import path
from apps.tickets import actions

app_name = 'tickets'

urlpatterns = [
    path('', actions.TicketListView.as_view(), name='list'),
]
