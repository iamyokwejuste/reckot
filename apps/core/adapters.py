import uuid
from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        if not user.username:
            email_prefix = user.email.split('@')[0] if user.email else 'user'
            user.username = f"{email_prefix}_{uuid.uuid4().hex[:8]}"
        return super().save_user(request, user, form, commit)
