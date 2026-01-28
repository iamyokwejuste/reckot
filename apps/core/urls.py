from django.urls import path
from apps.core import actions

app_name = 'core'

urlpatterns = [
    path('settings/', actions.SettingsView.as_view(), name='settings'),
]
