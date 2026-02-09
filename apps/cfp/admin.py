from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.cfp.models import (
    CallForProposals,
    SessionFormat,
    Track,
    SpeakerProfile,
    CFPQuestion,
    Proposal,
    ProposalQuestionAnswer,
    Review,
    Session,
)


@admin.register(CallForProposals)
class CallForProposalsAdmin(ModelAdmin):
    list_display = ("event", "status", "opens_at", "closes_at")
    list_filter = ("status",)
    search_fields = ("event__title",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(SessionFormat)
class SessionFormatAdmin(ModelAdmin):
    list_display = ("name", "event", "duration_minutes", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "event__title")


@admin.register(Track)
class TrackAdmin(ModelAdmin):
    list_display = ("name", "event", "color", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "event__title")


@admin.register(SpeakerProfile)
class SpeakerProfileAdmin(ModelAdmin):
    list_display = ("user", "event", "company", "job_title")
    search_fields = ("user__email", "user__first_name", "user__last_name", "company")


@admin.register(CFPQuestion)
class CFPQuestionAdmin(ModelAdmin):
    list_display = ("question", "cfp", "field_type", "is_required")
    list_filter = ("field_type", "is_required")


@admin.register(Proposal)
class ProposalAdmin(ModelAdmin):
    list_display = ("title", "speaker", "cfp", "status", "submitted_at")
    list_filter = ("status", "level")
    search_fields = ("title", "speaker__email")
    readonly_fields = ("submitted_at", "decided_at", "created_at", "updated_at")


@admin.register(ProposalQuestionAnswer)
class ProposalQuestionAnswerAdmin(ModelAdmin):
    list_display = ("proposal", "question")


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ("proposal", "reviewer", "rating", "created_at")
    list_filter = ("rating", "is_abstained")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Session)
class SessionAdmin(ModelAdmin):
    list_display = ("title", "event", "track", "room", "starts_at", "status")
    list_filter = ("status", "track")
    search_fields = ("title", "speaker__email")
    readonly_fields = ("created_at", "updated_at")
