from django.urls import path
from apps.orgs import actions

app_name = 'orgs'

urlpatterns = [
    path('', actions.OrganizationListView.as_view(), name='list'),
    path('create/', actions.OrganizationCreateView.as_view(), name='create'),
    path('invite/<uuid:token>/', actions.AcceptInvitationView.as_view(), name='accept_invitation'),
    path('<slug:slug>/', actions.OrganizationDetailView.as_view(), name='detail'),
    path('<slug:slug>/members/', actions.OrganizationMembersView.as_view(), name='members'),
    path('<slug:slug>/members/invite/', actions.InviteMemberView.as_view(), name='invite_member'),
    path('<slug:slug>/members/<int:user_id>/role/', actions.UpdateMemberRoleView.as_view(), name='update_member_role'),
    path('<slug:slug>/members/<int:user_id>/remove/', actions.RemoveMemberView.as_view(), name='remove_member'),
    path('<slug:slug>/leave/', actions.LeaveOrganizationView.as_view(), name='leave'),
    path('<slug:slug>/invitations/<int:invitation_id>/cancel/', actions.CancelInvitationView.as_view(), name='cancel_invitation'),
    path('<slug:slug>/invitations/<int:invitation_id>/resend/', actions.ResendInvitationView.as_view(), name='resend_invitation'),
    path('<slug:slug>/transfer-ownership/', actions.TransferOwnershipView.as_view(), name='transfer_ownership'),
]
