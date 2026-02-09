import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.cfp.models import Proposal
from apps.core.models import Notification
from apps.core.tasks import send_email_task
from apps.orgs.models import Membership, MemberRole

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_proposal_status_email_task(proposal_id):
    try:
        proposal = Proposal.objects.select_related(
            "cfp__event__organization", "speaker"
        ).get(id=proposal_id)

        event = proposal.cfp.event
        speaker = proposal.speaker

        template_map = {
            Proposal.Status.ACCEPTED: "emails/cfp_proposal_accepted.html",
            Proposal.Status.REJECTED: "emails/cfp_proposal_rejected.html",
            Proposal.Status.WAITLISTED: "emails/cfp_proposal_waitlisted.html",
        }

        subject_map = {
            Proposal.Status.ACCEPTED: f"Your proposal has been accepted - {event.title}",
            Proposal.Status.REJECTED: f"Update on your proposal - {event.title}",
            Proposal.Status.WAITLISTED: f"Your proposal has been waitlisted - {event.title}",
        }

        template = template_map.get(proposal.status)
        subject = subject_map.get(proposal.status)

        if not template or not subject:
            return

        context = {
            "proposal": {
                "title": proposal.title,
                "status": proposal.get_status_display(),
            },
            "event": {
                "title": event.title,
                "start_at": event.start_at.isoformat(),
            },
            "speaker_name": speaker.get_full_name() or speaker.email,
            "proposals_url": reverse(
                "cfp:speaker_proposals",
                kwargs={
                    "org_slug": event.organization.slug,
                    "event_slug": event.slug,
                },
            ),
        }

        send_email_task.delay(
            to_email=speaker.email,
            subject=subject,
            template_name=template,
            context=context,
        )

        notification_type_map = {
            Proposal.Status.ACCEPTED: Notification.Type.PROPOSAL_ACCEPTED,
            Proposal.Status.REJECTED: Notification.Type.PROPOSAL_REJECTED,
            Proposal.Status.WAITLISTED: Notification.Type.PROPOSAL_WAITLISTED,
        }

        notif_type = notification_type_map.get(proposal.status)
        if notif_type:
            Notification.objects.create(
                user=speaker,
                notification_type=notif_type,
                title=subject,
                message=f'Your proposal "{proposal.title}" for {event.title} has been {proposal.get_status_display().lower()}.',
                link=context["proposals_url"],
            )

        logger.info(
            f"Status email sent to {speaker.email} for proposal {proposal_id}"
        )
    except Exception as e:
        logger.error(f"Failed to send proposal status email: {e}")


@shared_task
def send_new_submission_notification_task(proposal_id):
    try:
        proposal = Proposal.objects.select_related(
            "cfp__event__organization", "speaker"
        ).get(id=proposal_id)

        event = proposal.cfp.event
        org = event.organization

        admin_memberships = Membership.objects.filter(
            organization=org,
            role__in=[MemberRole.OWNER, MemberRole.ADMIN],
        ).select_related("user")

        context = {
            "proposal": {
                "title": proposal.title,
                "speaker": proposal.speaker.get_full_name() or proposal.speaker.email,
            },
            "event": {"title": event.title},
            "manage_url": reverse(
                "cfp:proposal_detail",
                kwargs={
                    "org_slug": org.slug,
                    "event_slug": event.slug,
                    "id": proposal.id,
                },
            ),
        }

        for membership in admin_memberships:
            send_email_task.delay(
                to_email=membership.user.email,
                subject=f"New proposal submitted - {event.title}",
                template_name="emails/cfp_new_submission.html",
                context=context,
            )

            Notification.objects.create(
                user=membership.user,
                notification_type=Notification.Type.PROPOSAL_SUBMITTED,
                title=f"New proposal: {proposal.title}",
                message=f'{context["proposal"]["speaker"]} submitted "{proposal.title}" to {event.title}.',
                link=context["manage_url"],
            )

        logger.info(f"New submission notifications sent for proposal {proposal_id}")
    except Exception as e:
        logger.error(f"Failed to send new submission notification: {e}")


@shared_task
def send_submission_confirmation_task(proposal_id):
    try:
        proposal = Proposal.objects.select_related(
            "cfp__event__organization", "speaker"
        ).get(id=proposal_id)

        event = proposal.cfp.event
        speaker = proposal.speaker

        context = {
            "proposal": {"title": proposal.title},
            "event": {"title": event.title},
            "speaker_name": speaker.get_full_name() or speaker.email,
            "proposals_url": reverse(
                "cfp:speaker_proposals",
                kwargs={
                    "org_slug": event.organization.slug,
                    "event_slug": event.slug,
                },
            ),
        }

        send_email_task.delay(
            to_email=speaker.email,
            subject=f"Proposal received - {event.title}",
            template_name="emails/cfp_submission_confirmation.html",
            context=context,
        )

        logger.info(f"Submission confirmation sent to {speaker.email}")
    except Exception as e:
        logger.error(f"Failed to send submission confirmation: {e}")


@shared_task
def send_bulk_decision_emails_task(proposal_ids, action):
    for proposal_id in proposal_ids:
        send_proposal_status_email_task.delay(proposal_id)
