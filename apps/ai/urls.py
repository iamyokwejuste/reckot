from django.urls import path
from apps.ai import actions

app_name = 'ai'

urlpatterns = [
    path('assistant/', actions.AIAssistantView.as_view(), name='assistant'),
    path('assistant/chat/', actions.AIAssistantChatView.as_view(), name='chat'),
    path('assistant/clear/', actions.ClearConversationView.as_view(), name='clear'),
    path('generate/', actions.AIGenerateContentView.as_view(), name='generate'),
    path('analyze/', actions.AIAnalyzeIssueView.as_view(), name='analyze'),
    path('insights/<int:event_id>/', actions.AIEventInsightsView.as_view(), name='insights'),
    path('tickets/', actions.SupportTicketListView.as_view(), name='tickets'),
    path('tickets/create/', actions.SupportTicketCreateView.as_view(), name='ticket_create'),
    path('tickets/<uuid:reference>/', actions.SupportTicketDetailView.as_view(), name='ticket_detail'),
]
