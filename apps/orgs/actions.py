import csv
import io
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from apps.core.tasks import send_email_task
from apps.orgs.models import Organization, Membership, Invitation, MemberRole
from apps.payments.models import Payment
from apps.core.models import User

logger = logging.getLogger(__name__)


class OrgPermissionMixin:
    required_permission: str | None = None

    def get_organization(self, slug):
        return get_object_or_404(Organization, slug=slug)

    def check_permission(self, request, organization):
        if self.required_permission:
            if not organization.user_can(request.user, self.required_permission):
                return False
        return organization.members.filter(id=request.user.id).exists()

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        if slug:
            organization = self.get_organization(slug)
            if not self.check_permission(request, organization):
                messages.error(
                    request, _("You don't have permission to perform this action.")
                )
                return redirect("orgs:list")
            self.organization = organization
        return super().dispatch(request, *args, **kwargs)


class OrganizationListView(LoginRequiredMixin, View):
    def get(self, request):
        organizations = (
            Organization.objects.filter(members=request.user)
            .annotate(
                event_count=Count("events"),
                member_count=Count("members", distinct=True),
            )
            .order_by("name")
        )

        return render(
            request,
            "orgs/list.html",
            {
                "organizations": organizations,
            },
        )


class OrganizationCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "orgs/create.html")

    def post(self, request):
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        website = request.POST.get("website", "").strip()

        if not name:
            return render(
                request,
                "orgs/create.html",
                {
                    "error": _("Organization name is required."),
                },
            )

        try:
            organization = Organization.objects.create(
                name=name,
                description=description,
                website=website,
                owner=request.user,
            )

            if request.FILES.get("logo"):
                organization.logo = request.FILES["logo"]
                organization.save()

            Membership.objects.create(
                organization=organization,
                user=request.user,
                role=MemberRole.OWNER,
            )

            messages.success(
                request,
                _('Organization "%(name)s" created successfully!') % {"name": name},
            )
            return redirect("orgs:detail", slug=organization.slug)
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Failed to create organization: {e}")
            return render(
                request,
                "orgs/create.html",
                {
                    "error": _("Failed to create organization: %(error)s")
                    % {"error": str(e)},
                    "name": name,
                    "description": description,
                    "website": website,
                },
            )


class OrganizationDetailView(LoginRequiredMixin, OrgPermissionMixin, View):
    def get(self, request, slug):
        organization = self.organization
        events = organization.events.all().order_by("-start_at")[:10]
        memberships = (
            Membership.objects.filter(organization=organization)
            .select_related("user")
            .order_by("role", "created_at")
        )

        total_revenue = (
            Payment.objects.filter(
                booking__event__organization=organization,
                status=Payment.Status.CONFIRMED,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        user_membership = Membership.objects.filter(
            organization=organization, user=request.user
        ).first()

        can_manage_members = organization.user_can(request.user, "manage_members")
        can_invite = organization.user_can(request.user, "invite_members")

        return render(
            request,
            "orgs/detail.html",
            {
                "organization": organization,
                "events": events,
                "memberships": memberships,
                "total_revenue": total_revenue,
                "user_membership": user_membership,
                "can_manage_members": can_manage_members,
                "can_invite": can_invite,
            },
        )


class OrganizationMembersView(LoginRequiredMixin, OrgPermissionMixin, View):
    required_permission = "manage_members"

    def get(self, request, slug):
        organization = self.organization
        memberships = (
            Membership.objects.filter(organization=organization)
            .select_related("user", "invited_by")
            .order_by("role", "created_at")
        )

        pending_invitations = (
            Invitation.objects.filter(
                organization=organization, status=Invitation.Status.PENDING
            )
            .select_related("invited_by")
            .order_by("-created_at")
        )

        return render(
            request,
            "orgs/members.html",
            {
                "organization": organization,
                "memberships": memberships,
                "pending_invitations": pending_invitations,
                "roles": MemberRole.choices,
            },
        )


class InviteMemberView(LoginRequiredMixin, OrgPermissionMixin, View):
    required_permission = "invite_members"

    def get(self, request, slug):
        organization = self.organization
        return render(
            request,
            "orgs/invite_member.html",
            {
                "organization": organization,
                "roles": [r for r in MemberRole.choices if r[0] != MemberRole.OWNER],
            },
        )

    def post(self, request, slug):
        organization = self.organization
        email = request.POST.get("email", "").strip().lower()
        role = request.POST.get("role", MemberRole.MEMBER)
        message_text = request.POST.get("message", "").strip()

        if not email:
            messages.error(request, _("Email is required."))
            return redirect("orgs:invite_member", slug=slug)

        if role == MemberRole.OWNER:
            messages.error(request, _("Cannot invite users as Owner."))
            return redirect("orgs:invite_member", slug=slug)

        existing_user = User.objects.filter(email=email).first()
        if existing_user and organization.members.filter(id=existing_user.id).exists():
            messages.warning(
                request,
                _("%(email)s is already a member of this organization.")
                % {"email": email},
            )
            return redirect("orgs:members", slug=slug)

        existing_invitation = Invitation.objects.filter(
            organization=organization, email=email, status=Invitation.Status.PENDING
        ).first()

        if existing_invitation:
            messages.warning(
                request,
                _("An invitation has already been sent to %(email)s.")
                % {"email": email},
            )
            return redirect("orgs:members", slug=slug)

        invitation = Invitation.objects.create(
            organization=organization,
            email=email,
            role=role,
            message=message_text,
            invited_by=request.user,
        )

        try:
            invite_url = request.build_absolute_uri(f"/orgs/invite/{invitation.token}/")
            subject = f"You're invited to join {organization.name} on Reckot"
            send_email_task.delay(
                to_email=email,
                subject=subject,
                template_name="emails/invitation.html",
                context={
                    "organization": organization,
                    "invitation": invitation,
                    "invite_url": invite_url,
                    "inviter": request.user,
                },
            )
            messages.success(request, _("Invitation sent to %(email)s.") % {"email": email})
        except Exception as e:
            logger.error(f"Failed to queue invitation email to {email}: {e}", exc_info=True)
            messages.warning(
                request,
                _("Invitation created for %(email)s, but email notification failed. They can still use the invite link.")
                % {"email": email}
            )
        return redirect("orgs:members", slug=slug)


class UpdateMemberRoleView(LoginRequiredMixin, OrgPermissionMixin, View):
    required_permission = "manage_members"

    def post(self, request, slug, user_id):
        organization = self.organization
        new_role = request.POST.get("role")

        if new_role not in [r[0] for r in MemberRole.choices]:
            messages.error(request, _("Invalid role."))
            return redirect("orgs:members", slug=slug)

        membership = get_object_or_404(
            Membership, organization=organization, user_id=user_id
        )

        if membership.role == MemberRole.OWNER:
            messages.error(
                request, _("Cannot change the role of the organization owner.")
            )
            return redirect("orgs:members", slug=slug)

        if new_role == MemberRole.OWNER:
            messages.error(
                request, _("Cannot assign Owner role. Transfer ownership instead.")
            )
            return redirect("orgs:members", slug=slug)

        membership.role = new_role
        membership.save()

        messages.success(
            request,
            _("Updated %(email)s's role to %(role)s.")
            % {"email": membership.user.email, "role": membership.get_role_display()},
        )
        return redirect("orgs:members", slug=slug)


class RemoveMemberView(LoginRequiredMixin, OrgPermissionMixin, View):
    required_permission = "remove_members"

    def post(self, request, slug, user_id):
        organization = self.organization

        membership = get_object_or_404(
            Membership, organization=organization, user_id=user_id
        )

        if membership.role == MemberRole.OWNER:
            messages.error(request, _("Cannot remove the organization owner."))
            return redirect("orgs:members", slug=slug)

        if membership.user == request.user:
            messages.error(
                request,
                _("You cannot remove yourself. Leave the organization instead."),
            )
            return redirect("orgs:members", slug=slug)

        user_email = membership.user.email
        membership.delete()

        messages.success(
            request,
            _("Removed %(email)s from the organization.") % {"email": user_email},
        )
        return redirect("orgs:members", slug=slug)


class LeaveOrganizationView(LoginRequiredMixin, View):
    def post(self, request, slug):
        organization = get_object_or_404(Organization, slug=slug)

        if organization.owner == request.user:
            messages.error(
                request,
                _(
                    "As the owner, you cannot leave the organization. Transfer ownership first."
                ),
            )
            return redirect("orgs:detail", slug=slug)

        membership = Membership.objects.filter(
            organization=organization, user=request.user
        ).first()

        if membership:
            membership.delete()
            messages.success(
                request, _("You have left %(name)s.") % {"name": organization.name}
            )

        return redirect("orgs:list")


class CancelInvitationView(LoginRequiredMixin, OrgPermissionMixin, View):
    required_permission = "invite_members"

    def post(self, request, slug, invitation_id):
        organization = self.organization

        invitation = get_object_or_404(
            Invitation,
            id=invitation_id,
            organization=organization,
            status=Invitation.Status.PENDING,
        )

        invitation.cancel()
        messages.success(
            request,
            _("Cancelled invitation to %(email)s.") % {"email": invitation.email},
        )
        return redirect("orgs:members", slug=slug)


class ResendInvitationView(LoginRequiredMixin, OrgPermissionMixin, View):
    required_permission = "invite_members"

    def post(self, request, slug, invitation_id):
        organization = self.organization

        invitation = get_object_or_404(
            Invitation,
            id=invitation_id,
            organization=organization,
            status=Invitation.Status.PENDING,
        )

        try:
            invite_url = request.build_absolute_uri(f"/orgs/invite/{invitation.token}/")
            subject = f"Reminder: You're invited to join {organization.name} on Reckot"
            send_email_task.delay(
                to_email=invitation.email,
                subject=subject,
                template_name="emails/invitation.html",
                context={
                    "organization": organization,
                    "invitation": invitation,
                    "invite_url": invite_url,
                    "inviter": request.user,
                },
            )
            messages.success(
                request,
                _("Invitation resent to %(email)s.") % {"email": invitation.email},
            )
        except Exception:
            messages.error(request, _("Failed to resend invitation."))

        return redirect("orgs:members", slug=slug)


class AcceptInvitationView(LoginRequiredMixin, View):
    def get(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)

        if invitation.status != Invitation.Status.PENDING:
            return render(
                request,
                "orgs/invitation_error.html",
                {"message": _("This invitation has already been used or cancelled.")},
            )

        if invitation.is_expired:
            invitation.status = Invitation.Status.EXPIRED
            invitation.save()
            return render(
                request,
                "orgs/invitation_error.html",
                {"message": _("This invitation has expired.")},
            )

        return render(
            request,
            "orgs/accept_invitation.html",
            {
                "invitation": invitation,
            },
        )

    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)

        if not invitation.is_valid:
            return render(
                request,
                "orgs/invitation_error.html",
                {"message": _("This invitation is no longer valid.")},
            )

        membership = invitation.accept(request.user)

        if membership:
            messages.success(
                request,
                _("Welcome to %(name)s!") % {"name": invitation.organization.name},
            )
            return redirect("orgs:detail", slug=invitation.organization.slug)
        else:
            return render(
                request,
                "orgs/invitation_error.html",
                {"message": _("Failed to accept invitation.")},
            )


class TransferOwnershipView(LoginRequiredMixin, View):
    def post(self, request, slug):
        organization = get_object_or_404(Organization, slug=slug, owner=request.user)
        new_owner_id = request.POST.get("new_owner_id")

        if not new_owner_id:
            messages.error(request, _("Please select a new owner."))
            return redirect("orgs:members", slug=slug)

        new_owner_membership = get_object_or_404(
            Membership, organization=organization, user_id=new_owner_id
        )

        old_owner_membership = Membership.objects.get(
            organization=organization, user=request.user
        )
        old_owner_membership.role = MemberRole.ADMIN
        old_owner_membership.save()

        new_owner_membership.role = MemberRole.OWNER
        new_owner_membership.save()

        organization.owner = new_owner_membership.user
        organization.save()

        messages.success(
            request,
            _("Ownership transferred to %(email)s.")
            % {"email": new_owner_membership.user.email},
        )
        return redirect("orgs:detail", slug=slug)


class OrganizationEditView(LoginRequiredMixin, OrgPermissionMixin, View):
    required_permission = "manage_organization"

    def get(self, request, slug):
        organization = self.organization
        return render(
            request,
            "orgs/edit.html",
            {
                "organization": organization,
            },
        )

    def post(self, request, slug):
        organization = self.organization
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        website = request.POST.get("website", "").strip()

        if not name:
            return render(
                request,
                "orgs/edit.html",
                {
                    "organization": organization,
                    "error": _("Organization name is required."),
                },
            )

        organization.name = name
        organization.description = description
        organization.website = website

        if request.FILES.get("logo"):
            organization.logo = request.FILES["logo"]

        if request.POST.get("remove_logo") == "true":
            organization.logo = None

        organization.save()

        messages.success(request, _("Organization updated successfully!"))
        return redirect("orgs:detail", slug=organization.slug)


class BulkInviteView(LoginRequiredMixin, OrgPermissionMixin, View):
    required_permission = "invite_members"

    def get(self, request, slug):
        organization = self.organization
        return render(
            request,
            "orgs/bulk_invite.html",
            {
                "organization": organization,
                "roles": [r for r in MemberRole.choices if r[0] != MemberRole.OWNER],
            },
        )

    def post(self, request, slug):
        organization = self.organization
        role = request.POST.get("role", MemberRole.MEMBER)
        message_text = request.POST.get("message", "").strip()

        if role == MemberRole.OWNER:
            messages.error(request, _("Cannot invite users as Owner."))
            return redirect("orgs:bulk_invite", slug=slug)

        csv_file = request.FILES.get("csv_file")
        emails_text = request.POST.get("emails", "").strip()

        emails = []

        if csv_file:
            try:
                decoded = csv_file.read().decode("utf-8")
                reader = csv.reader(io.StringIO(decoded))
                for row in reader:
                    if row:
                        email = row[0].strip().lower()
                        if "@" in email and email not in emails:
                            emails.append(email)
            except Exception:
                messages.error(request, _("Failed to parse CSV file."))
                return redirect("orgs:bulk_invite", slug=slug)

        if emails_text:
            for line in emails_text.replace(",", "\n").split("\n"):
                email = line.strip().lower()
                if "@" in email and email not in emails:
                    emails.append(email)

        if not emails:
            messages.error(request, _("No valid emails found."))
            return redirect("orgs:bulk_invite", slug=slug)

        sent_count = 0
        skipped_count = 0

        for email in emails:
            existing_user = User.objects.filter(email=email).first()
            if (
                existing_user
                and organization.members.filter(id=existing_user.id).exists()
            ):
                skipped_count += 1
                continue

            existing_invitation = Invitation.objects.filter(
                organization=organization, email=email, status=Invitation.Status.PENDING
            ).exists()

            if existing_invitation:
                skipped_count += 1
                continue

            invitation = Invitation.objects.create(
                organization=organization,
                email=email,
                role=role,
                message=message_text,
                invited_by=request.user,
            )

            try:
                invite_url = request.build_absolute_uri(
                    f"/orgs/invite/{invitation.token}/"
                )
                subject = f"You're invited to join {organization.name} on Reckot"
                send_email_task.delay(
                    to_email=email,
                    subject=subject,
                    template_name="emails/invitation.html",
                    context={
                        "organization": organization,
                        "invitation": invitation,
                        "invite_url": invite_url,
                        "inviter": request.user,
                    },
                )
                sent_count += 1
            except Exception:
                sent_count += 1

        if sent_count > 0:
            messages.success(
                request, _("Sent %(count)d invitation(s).") % {"count": sent_count}
            )
        if skipped_count > 0:
            messages.info(
                request,
                _("Skipped %(count)d existing member(s) or pending invitation(s).")
                % {"count": skipped_count},
            )

        return redirect("orgs:members", slug=slug)


class DownloadInviteTemplateView(LoginRequiredMixin, View):
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="invite_template.csv"'
        writer = csv.writer(response)
        writer.writerow(["email"])
        writer.writerow(["user1@example.com"])
        writer.writerow(["user2@example.com"])
        return response


class OrganizationDeleteView(LoginRequiredMixin, OrgPermissionMixin, View):
    required_permission = "delete_organization"

    def post(self, request, slug):
        organization = get_object_or_404(Organization, slug=slug)

        if organization.owner != request.user:
            messages.error(request, _("Only the organization owner can delete it."))
            return redirect("orgs:detail", slug=slug)

        org_name = organization.name
        organization.delete()

        messages.success(
            request,
            _("Organization '{}' has been deleted successfully.").format(org_name),
        )
        return redirect("orgs:list")
