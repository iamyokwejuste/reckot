from django.urls import path

from apps.cfp.views import organizer, public, speaker

app_name = "cfp"

urlpatterns = [
    # Public CFP page
    path(
        "<slug:org_slug>/<slug:event_slug>/cfp/",
        public.PublicCFPView.as_view(),
        name="public_cfp",
    ),
    # Public schedule
    path(
        "<slug:org_slug>/<slug:event_slug>/schedule/",
        public.PublicScheduleView.as_view(),
        name="public_schedule",
    ),
    path(
        "<slug:org_slug>/<slug:event_slug>/schedule/<int:id>/",
        public.PublicSessionDetailView.as_view(),
        name="public_session",
    ),
    # Public speakers
    path(
        "<slug:org_slug>/<slug:event_slug>/speakers/",
        public.PublicSpeakerListView.as_view(),
        name="public_speakers",
    ),
    # Speaker: submit proposal
    path(
        "<slug:org_slug>/<slug:event_slug>/cfp/submit/",
        speaker.CFPSubmitView.as_view(),
        name="submit_proposal",
    ),
    # Speaker: proposals list
    path(
        "<slug:org_slug>/<slug:event_slug>/cfp/proposals/",
        speaker.SpeakerProposalsView.as_view(),
        name="speaker_proposals",
    ),
    # Speaker: edit proposal
    path(
        "<slug:org_slug>/<slug:event_slug>/cfp/proposals/<int:id>/",
        speaker.ProposalEditView.as_view(),
        name="proposal_edit",
    ),
    # Speaker: confirm accepted proposal
    path(
        "<slug:org_slug>/<slug:event_slug>/cfp/proposals/<int:id>/confirm/",
        speaker.ProposalConfirmView.as_view(),
        name="proposal_confirm",
    ),
    # Speaker: withdraw proposal
    path(
        "<slug:org_slug>/<slug:event_slug>/cfp/proposals/<int:id>/withdraw/",
        speaker.ProposalWithdrawView.as_view(),
        name="proposal_withdraw",
    ),
    # Speaker: profile
    path(
        "<slug:org_slug>/<slug:event_slug>/cfp/profile/",
        speaker.SpeakerProfileView.as_view(),
        name="speaker_profile",
    ),
    # Organizer: CFP config
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/",
        organizer.CFPConfigView.as_view(),
        name="cfp_config",
    ),
    # Organizer: session formats
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/formats/",
        organizer.SessionFormatManageView.as_view(),
        name="session_formats",
    ),
    # Organizer: tracks
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/tracks/",
        organizer.TrackManageView.as_view(),
        name="tracks",
    ),
    # Organizer: custom questions
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/questions/",
        organizer.CFPQuestionsView.as_view(),
        name="cfp_questions",
    ),
    # Organizer: proposals list
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/proposals/",
        organizer.ProposalListView.as_view(),
        name="proposals_list",
    ),
    # Organizer: proposal detail
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/proposals/<int:id>/",
        organizer.ProposalDetailView.as_view(),
        name="proposal_detail",
    ),
    # Organizer: submit review
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/proposals/<int:id>/review/",
        organizer.ProposalReviewView.as_view(),
        name="proposal_review",
    ),
    # Organizer: decide on proposal
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/proposals/<int:id>/decide/",
        organizer.ProposalDecideView.as_view(),
        name="proposal_decide",
    ),
    # Organizer: bulk action
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/proposals/bulk-action/",
        organizer.BulkActionView.as_view(),
        name="bulk_action",
    ),
    # Organizer: export proposals
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/proposals/export/",
        organizer.ExportProposalsView.as_view(),
        name="export_proposals",
    ),
    # Organizer: CFP analytics
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/cfp/analytics/",
        organizer.CFPAnalyticsView.as_view(),
        name="cfp_analytics",
    ),
    # Organizer: schedule builder
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/schedule/",
        organizer.ScheduleBuilderView.as_view(),
        name="schedule_builder",
    ),
    # Organizer: schedule save API
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/schedule/update/",
        organizer.ScheduleUpdateView.as_view(),
        name="schedule_update",
    ),
    # Organizer: edit session
    path(
        "<slug:org_slug>/<slug:event_slug>/manage/schedule/<int:id>/edit/",
        organizer.SessionEditView.as_view(),
        name="session_edit",
    ),
]
