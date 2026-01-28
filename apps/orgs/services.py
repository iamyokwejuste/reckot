from django.urls import reverse
from django.contrib.sites.models import Site
from apps.orgs.models import Invitation, Organization, Membership, Role

def send_invitation(organization: Organization, invited_by, email: str, role: Role):
    invitation = Invitation.objects.create(
        organization=organization,
        invited_by=invited_by,
        email=email,
        role=role,
    )
    current_site = Site.objects.get_current()
    invite_link = reverse('orgs:accept_invitation', kwargs={'token': invitation.token})
    full_invite_link = f'http://{current_site.domain}{invite_link}'
    return invitation, full_invite_link

def accept_invitation(token: str, user):
    try:
        invitation = Invitation.objects.get(token=token)
    except Invitation.DoesNotExist:
        return False, "Invitation not found."

    if invitation.is_expired():
        return False, "Invitation has expired."

    if Membership.objects.filter(organization=invitation.organization, user=user).exists():
        return False, "You are already a member of this organization."

    Membership.objects.create(
        organization=invitation.organization,
        user=user,
        role=invitation.role,
    )
    invitation.delete()
    return True, "Invitation accepted."