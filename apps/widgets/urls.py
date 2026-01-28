from django.urls import path
from apps.widgets import actions

app_name = 'widgets'

urlpatterns = [
    path('<uuid:widget_id>/', actions.WidgetView.as_view(), name='embed'),
    path('<uuid:widget_id>/embed.js', actions.WidgetJSView.as_view(), name='embed_js'),
    path('<uuid:widget_id>/config/', actions.WidgetConfigView.as_view(), name='config'),
]
