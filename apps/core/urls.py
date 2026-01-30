from django.urls import path
from apps.core import actions
from apps.core.api import ai

app_name = "core"

urlpatterns = [
    path("settings/", actions.SettingsView.as_view(), name="settings"),
    path(
        "settings/toggle-ai/",
        actions.ToggleAIFeaturesView.as_view(),
        name="toggle_ai_features",
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
