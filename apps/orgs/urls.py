from django.urls import path
from . import actions

app_name = 'orgs'

urlpatterns = [
    # path('create/', actions.OrganizationCreateView.as_view(), name='create'), # Placeholder for later
    path('invite/<uuid:token>/', actions.AcceptInvitationView.as_view(), name='accept_invitation'),
]
