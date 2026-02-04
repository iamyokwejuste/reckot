from django.urls import path
from apps.core.views import actions, notification_views
from apps.core.api import ai

app_name = "core"

urlpatterns = [
    path(
        "api/notifications/",
        notification_views.NotificationListView.as_view(),
        name="notifications_list",
    ),
    path(
        "api/notifications/<int:notification_id>/read/",
        notification_views.NotificationMarkReadView.as_view(),
        name="notification_mark_read",
    ),
    path(
        "api/notifications/read-all/",
        notification_views.NotificationMarkAllReadView.as_view(),
        name="notifications_mark_all_read",
    ),
    path("settings/", actions.SettingsView.as_view(), name="settings"),
    path(
        "settings/toggle-ai/",
        actions.ToggleAIFeaturesView.as_view(),
        name="toggle_ai_features",
    ),
    path(
        "settings/delete-account/",
        actions.DeleteAccountView.as_view(),
        name="delete_account",
    ),
    path(
        "api/ai/generate-description/",
        ai.generate_description,
        name="ai_generate_description",
    ),
    path(
        "api/ai/improve-description/",
        ai.improve_description,
        name="ai_improve_description",
    ),
    path("api/ai/generate-seo/", ai.generate_seo, name="ai_generate_seo"),
    path(
        "api/ai/generate-caption/",
        ai.generate_social_caption,
        name="ai_generate_caption",
    ),
    path("api/ai/translate/", ai.translate_text, name="ai_translate"),
    path("api/ai/summarize/", ai.summarize_text, name="ai_summarize"),
    path("api/ai/suggest-pricing/", ai.suggest_pricing, name="ai_suggest_pricing"),
    path("api/ai/suggest-tags/", ai.suggest_tags, name="ai_suggest_tags"),
    path("api/ai/assistant/", ai.event_assistant, name="ai_assistant"),
    path("api/ai/insight/", ai.generate_insight, name="ai_insight"),
]
