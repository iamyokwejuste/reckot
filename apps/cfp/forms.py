from django import forms
from django.utils.translation import gettext_lazy as _

from apps.cfp.models import (
    CallForProposals,
    SessionFormat,
    Track,
    CFPQuestion,
    SpeakerProfile,
    Proposal,
    Review,
    Session,
)


class CFPConfigForm(forms.ModelForm):
    class Meta:
        model = CallForProposals
        fields = [
            "title",
            "description",
            "opens_at",
            "closes_at",
            "max_submissions_per_speaker",
            "anonymous_review",
            "allow_edits_after_submit",
            "notify_on_submission",
        ]
        widgets = {
            "opens_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "closes_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        opens_at = cleaned_data.get("opens_at")
        closes_at = cleaned_data.get("closes_at")
        if opens_at and closes_at and opens_at >= closes_at:
            raise forms.ValidationError(
                _("Closing date must be after opening date.")
            )
        return cleaned_data


class SessionFormatForm(forms.ModelForm):
    class Meta:
        model = SessionFormat
        fields = [
            "name",
            "duration_minutes",
            "description",
            "max_capacity",
            "display_order",
            "is_active",
        ]


class TrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = [
            "name",
            "description",
            "color",
            "display_order",
            "is_active",
        ]
        widgets = {
            "color": forms.TextInput(attrs={"type": "color"}),
        }


class CFPQuestionForm(forms.ModelForm):
    class Meta:
        model = CFPQuestion
        fields = [
            "question",
            "field_type",
            "options",
            "is_required",
            "display_order",
        ]

    def clean_options(self):
        options = self.cleaned_data.get("options")
        field_type = self.cleaned_data.get("field_type")
        if field_type in ("SELECT", "RADIO", "CHECKBOX") and not options:
            raise forms.ValidationError(
                _("Options are required for this field type.")
            )
        return options


class SpeakerProfileForm(forms.ModelForm):
    class Meta:
        model = SpeakerProfile
        fields = [
            "bio",
            "tagline",
            "photo",
            "company",
            "job_title",
            "website",
            "twitter",
            "linkedin",
            "github",
            "travel_assistance",
            "accommodation_needed",
            "dietary_requirements",
            "custom_fields",
        ]
        widgets = {
            "custom_fields": forms.HiddenInput(),
        }


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = [
            "title",
            "abstract",
            "description",
            "outline",
            "session_format",
            "track",
            "level",
            "language",
            "tags",
            "speaker_notes",
        ]

    co_speaker_emails = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text=_("Comma-separated email addresses of co-speakers"),
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = [
            "rating",
            "content_score",
            "relevance_score",
            "speaker_score",
            "comment",
            "is_abstained",
        ]


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            "title",
            "description",
            "track",
            "room",
            "starts_at",
            "ends_at",
            "status",
        ]
        widgets = {
            "starts_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "ends_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }
