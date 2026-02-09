from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.cfp.forms import ProposalForm, SpeakerProfileForm
from apps.cfp.models import (
    CallForProposals,
    CFPQuestion,
    Proposal,
    ProposalQuestionAnswer,
    SpeakerProfile,
)
from apps.cfp.services.cfp_service import create_session_from_proposal
from apps.cfp.tasks import (
    send_new_submission_notification_task,
    send_submission_confirmation_task,
)
from apps.core.models import User
from apps.events.models import Event


def get_event_and_cfp(org_slug, event_slug):
    """Helper to resolve event and its CFP."""
    event = get_object_or_404(
        Event.objects.select_related("organization"),
        organization__slug=org_slug,
        slug=event_slug,
    )
    cfp = getattr(event, "cfp", None)
    return event, cfp


class CFPSubmitView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, cfp = get_event_and_cfp(org_slug, event_slug)
        if not cfp or not cfp.is_open:
            messages.warning(request, _("This call for proposals is not currently open."))
            return redirect(
                "cfp:public_cfp", org_slug=org_slug, event_slug=event_slug
            )

        submission_count = Proposal.objects.filter(
            cfp=cfp, speaker=request.user
        ).exclude(status=Proposal.Status.DRAFT).count()

        if submission_count >= cfp.max_submissions_per_speaker:
            messages.warning(
                request,
                _("You have reached the maximum number of submissions for this event."),
            )
            return redirect(
                "cfp:speaker_proposals", org_slug=org_slug, event_slug=event_slug
            )

        speaker_profile, _ = SpeakerProfile.objects.get_or_create(
            user=request.user, event=event,
            defaults={"bio": ""},
        )
        profile_form = SpeakerProfileForm(instance=speaker_profile)
        proposal_form = ProposalForm()
        proposal_form.fields["session_format"].queryset = event.session_formats.filter(is_active=True)
        proposal_form.fields["track"].queryset = event.tracks.filter(is_active=True)

        custom_questions = cfp.questions.all()

        return render(request, "cfp/submit_proposal.html", {
            "event": event,
            "cfp": cfp,
            "profile_form": profile_form,
            "proposal_form": proposal_form,
            "custom_questions": custom_questions,
            "speaker_profile": speaker_profile,
        })

    def post(self, request, org_slug, event_slug):
        event, cfp = get_event_and_cfp(org_slug, event_slug)
        if not cfp or not cfp.is_open:
            messages.warning(request, _("This call for proposals is not currently open."))
            return redirect(
                "cfp:public_cfp", org_slug=org_slug, event_slug=event_slug
            )

        submission_count = Proposal.objects.filter(
            cfp=cfp, speaker=request.user
        ).exclude(status=Proposal.Status.DRAFT).count()

        if submission_count >= cfp.max_submissions_per_speaker:
            messages.warning(
                request,
                _("You have reached the maximum number of submissions for this event."),
            )
            return redirect(
                "cfp:speaker_proposals", org_slug=org_slug, event_slug=event_slug
            )

        speaker_profile, _ = SpeakerProfile.objects.get_or_create(
            user=request.user, event=event,
            defaults={"bio": ""},
        )
        profile_form = SpeakerProfileForm(
            request.POST, request.FILES, instance=speaker_profile
        )
        proposal_form = ProposalForm(request.POST)
        proposal_form.fields["session_format"].queryset = event.session_formats.filter(is_active=True)
        proposal_form.fields["track"].queryset = event.tracks.filter(is_active=True)

        custom_questions = cfp.questions.all()

        if profile_form.is_valid() and proposal_form.is_valid():
            profile_form.save()

            proposal = proposal_form.save(commit=False)
            proposal.cfp = cfp
            proposal.speaker = request.user
            proposal.status = Proposal.Status.SUBMITTED
            proposal.submitted_at = timezone.now()
            proposal.save()

            co_emails = proposal_form.cleaned_data.get("co_speaker_emails", "")
            if co_emails:
                emails = [e.strip() for e in co_emails.split(",") if e.strip()]
                co_users = User.objects.filter(email__in=emails)
                proposal.co_speakers.set(co_users)

            for question in custom_questions:
                answer = request.POST.get(f"question_{question.id}", "")
                if answer or question.is_required:
                    ProposalQuestionAnswer.objects.create(
                        proposal=proposal,
                        question=question,
                        answer=answer,
                    )

            if request.user.active_mode == User.UserMode.ATTENDEE:
                request.user.active_mode = User.UserMode.SPEAKER
                request.user.save(update_fields=["active_mode"])

            send_submission_confirmation_task.delay(proposal.id)
            if cfp.notify_on_submission:
                send_new_submission_notification_task.delay(proposal.id)

            messages.success(request, _("Your proposal has been submitted successfully."))
            return redirect(
                "cfp:speaker_proposals", org_slug=org_slug, event_slug=event_slug
            )

        return render(request, "cfp/submit_proposal.html", {
            "event": event,
            "cfp": cfp,
            "profile_form": profile_form,
            "proposal_form": proposal_form,
            "custom_questions": custom_questions,
            "speaker_profile": speaker_profile,
        })


class SpeakerProposalsView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, cfp = get_event_and_cfp(org_slug, event_slug)

        proposals = Proposal.objects.filter(
            cfp__event=event, speaker=request.user
        ).select_related("session_format", "track").order_by("-submitted_at")

        return render(request, "cfp/speaker_proposals.html", {
            "event": event,
            "cfp": cfp,
            "proposals": proposals,
        })


class ProposalEditView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug, id):
        event, cfp = get_event_and_cfp(org_slug, event_slug)
        proposal = get_object_or_404(
            Proposal, id=id, cfp__event=event, speaker=request.user
        )

        if not cfp or (not cfp.allow_edits_after_submit and proposal.status != Proposal.Status.DRAFT):
            messages.warning(request, _("Editing is not allowed for this proposal."))
            return redirect(
                "cfp:speaker_proposals", org_slug=org_slug, event_slug=event_slug
            )

        form = ProposalForm(instance=proposal)
        form.fields["session_format"].queryset = event.session_formats.filter(is_active=True)
        form.fields["track"].queryset = event.tracks.filter(is_active=True)

        answers = {
            a.question_id: a.answer
            for a in proposal.question_answers.all()
        }
        custom_questions = cfp.questions.all() if cfp else []

        return render(request, "cfp/proposal_edit.html", {
            "event": event,
            "cfp": cfp,
            "proposal": proposal,
            "form": form,
            "custom_questions": custom_questions,
            "answers": answers,
        })

    def post(self, request, org_slug, event_slug, id):
        event, cfp = get_event_and_cfp(org_slug, event_slug)
        proposal = get_object_or_404(
            Proposal, id=id, cfp__event=event, speaker=request.user
        )

        if not cfp or (not cfp.allow_edits_after_submit and proposal.status != Proposal.Status.DRAFT):
            messages.warning(request, _("Editing is not allowed for this proposal."))
            return redirect(
                "cfp:speaker_proposals", org_slug=org_slug, event_slug=event_slug
            )

        form = ProposalForm(request.POST, instance=proposal)
        form.fields["session_format"].queryset = event.session_formats.filter(is_active=True)
        form.fields["track"].queryset = event.tracks.filter(is_active=True)

        if form.is_valid():
            form.save()

            co_emails = form.cleaned_data.get("co_speaker_emails", "")
            if co_emails:
                emails = [e.strip() for e in co_emails.split(",") if e.strip()]
                co_users = User.objects.filter(email__in=emails)
                proposal.co_speakers.set(co_users)

            custom_questions = cfp.questions.all()
            for question in custom_questions:
                answer = request.POST.get(f"question_{question.id}", "")
                ProposalQuestionAnswer.objects.update_or_create(
                    proposal=proposal,
                    question=question,
                    defaults={"answer": answer},
                )

            messages.success(request, _("Proposal updated."))
            return redirect(
                "cfp:speaker_proposals", org_slug=org_slug, event_slug=event_slug
            )

        custom_questions = cfp.questions.all() if cfp else []
        answers = {a.question_id: a.answer for a in proposal.question_answers.all()}

        return render(request, "cfp/proposal_edit.html", {
            "event": event,
            "cfp": cfp,
            "proposal": proposal,
            "form": form,
            "custom_questions": custom_questions,
            "answers": answers,
        })


class SpeakerProfileView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event, cfp = get_event_and_cfp(org_slug, event_slug)
        speaker_profile, _ = SpeakerProfile.objects.get_or_create(
            user=request.user, event=event,
            defaults={"bio": ""},
        )
        form = SpeakerProfileForm(instance=speaker_profile)

        return render(request, "cfp/speaker_profile.html", {
            "event": event,
            "form": form,
            "speaker_profile": speaker_profile,
        })

    def post(self, request, org_slug, event_slug):
        event, cfp = get_event_and_cfp(org_slug, event_slug)
        speaker_profile, _ = SpeakerProfile.objects.get_or_create(
            user=request.user, event=event,
            defaults={"bio": ""},
        )
        form = SpeakerProfileForm(
            request.POST, request.FILES, instance=speaker_profile
        )

        if form.is_valid():
            form.save()
            messages.success(request, _("Speaker profile updated."))
            return redirect(
                "cfp:speaker_profile", org_slug=org_slug, event_slug=event_slug
            )

        return render(request, "cfp/speaker_profile.html", {
            "event": event,
            "form": form,
            "speaker_profile": speaker_profile,
        })


class ProposalConfirmView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug, id):
        event, cfp = get_event_and_cfp(org_slug, event_slug)
        proposal = get_object_or_404(
            Proposal, id=id, cfp__event=event, speaker=request.user,
            status=Proposal.Status.ACCEPTED,
        )

        proposal.status = Proposal.Status.CONFIRMED
        proposal.save(update_fields=["status"])

        create_session_from_proposal(proposal)

        messages.success(request, _("You have confirmed your participation."))
        return redirect(
            "cfp:speaker_proposals", org_slug=org_slug, event_slug=event_slug
        )


class ProposalWithdrawView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug, id):
        event, cfp = get_event_and_cfp(org_slug, event_slug)
        proposal = get_object_or_404(
            Proposal, id=id, cfp__event=event, speaker=request.user,
        )

        if proposal.status in (Proposal.Status.REJECTED, Proposal.Status.WITHDRAWN):
            messages.warning(request, _("This proposal cannot be withdrawn."))
            return redirect(
                "cfp:speaker_proposals", org_slug=org_slug, event_slug=event_slug
            )

        proposal.status = Proposal.Status.WITHDRAWN
        proposal.save(update_fields=["status"])

        messages.success(request, _("Your proposal has been withdrawn."))
        return redirect(
            "cfp:speaker_proposals", org_slug=org_slug, event_slug=event_slug
        )


class SpeakerDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        proposals = Proposal.objects.filter(
            speaker=request.user
        ).select_related(
            "cfp__event__organization", "session_format", "track"
        ).order_by("-submitted_at")

        profiles = SpeakerProfile.objects.filter(
            user=request.user
        ).select_related("event__organization")

        total = proposals.count()
        accepted = proposals.filter(
            status__in=[Proposal.Status.ACCEPTED, Proposal.Status.CONFIRMED]
        ).count()
        pending = proposals.filter(
            status__in=[Proposal.Status.SUBMITTED, Proposal.Status.UNDER_REVIEW]
        ).count()

        upcoming_sessions = request.user.sessions.filter(
            status="SCHEDULED",
            starts_at__gte=timezone.now(),
        ).select_related("event", "track").order_by("starts_at")[:5]

        return render(request, "cfp/speaker_dashboard.html", {
            "proposals": proposals,
            "profiles": profiles,
            "stats": {
                "total": total,
                "accepted": accepted,
                "pending": pending,
            },
            "upcoming_sessions": upcoming_sessions,
        })
