from django.urls import path
from apps.ai.views import actions, hackathon_views, ai_query_views

app_name = "ai"

urlpatterns = [
    path("query/public/", ai_query_views.AIQueryPublicView.as_view(), name="query_public"),
    path("query/authenticated/", ai_query_views.AIQueryAuthenticatedView.as_view(), name="query_authenticated"),
    path("query/validate/", ai_query_views.AIQueryValidateView.as_view(), name="query_validate"),
    path("query/generate-sql/", ai_query_views.AIGenerateSQLView.as_view(), name="generate_sql"),
    path("query/schema-info/", ai_query_views.AISchemaInfoView.as_view(), name="schema_info"),
    path("assistant/chat/", actions.AIAssistantChatView.as_view(), name="chat"),
    path("assistant/clear/", actions.ClearConversationView.as_view(), name="clear"),
    path("assistant/transcribe/", actions.AudioTranscribeView.as_view(), name="transcribe"),
    path("generate/", actions.AIGenerateContentView.as_view(), name="generate"),
    path("analyze/", actions.AIAnalyzeIssueView.as_view(), name="analyze"),
    path(
        "insights/<int:event_id>/",
        actions.AIEventInsightsView.as_view(),
        name="insights",
    ),
    path("tickets/", actions.SupportTicketListView.as_view(), name="tickets"),
    path(
        "tickets/create/",
        actions.SupportTicketCreateView.as_view(),
        name="ticket_create",
    ),
    path(
        "tickets/<uuid:reference>/",
        actions.SupportTicketDetailView.as_view(),
        name="ticket_detail",
    ),
    path(
        "verify-event/", hackathon_views.VerifyEventView.as_view(), name="verify_event"
    ),
    path(
        "fraud-prevention-tips/",
        hackathon_views.FraudPreventionTipsView.as_view(),
        name="fraud_prevention_tips",
    ),
    path(
        "voice-to-event/",
        hackathon_views.VoiceToEventView.as_view(),
        name="voice_to_event",
    ),
    path(
        "predict-sales/",
        hackathon_views.PredictSalesView.as_view(),
        name="predict_sales",
    ),
    path(
        "optimize-pricing/",
        hackathon_views.OptimizePricingView.as_view(),
        name="optimize_pricing",
    ),
    path(
        "marketing-strategy/",
        hackathon_views.MarketingStrategyView.as_view(),
        name="marketing_strategy",
    ),
    path(
        "generate-cover-image/",
        hackathon_views.GenerateCoverImageView.as_view(),
        name="generate_cover_image",
    ),
    path("demo/", hackathon_views.AIFeaturesDemoView.as_view(), name="demo"),
    path(
        "event-concierge/<slug:org_slug>/<slug:event_slug>/",
        hackathon_views.EventConciergeView.as_view(),
        name="event_concierge",
    ),
    path(
        "event-concierge/<slug:org_slug>/<slug:event_slug>/audit/",
        hackathon_views.EventConciergeAuditView.as_view(),
        name="event_concierge_audit",
    ),
    path(
        "smart-scanner/",
        hackathon_views.SmartEventScannerView.as_view(),
        name="smart_scanner",
    ),
    path(
        "metrics/dashboard/",
        hackathon_views.AIMetricsDashboardView.as_view(),
        name="metrics_dashboard",
    ),
    path(
        "assistant/chat/stream/",
        hackathon_views.StreamingChatView.as_view(),
        name="streaming_chat",
    ),
    path(
        "low-bandwidth/",
        hackathon_views.LowBandwidthModeView.as_view(),
        name="low_bandwidth",
    ),
    path(
        "community-templates/",
        hackathon_views.CommunityTemplateView.as_view(),
        name="community_templates",
    ),
]
