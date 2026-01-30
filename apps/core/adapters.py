from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.contrib import messages
from django.shortcuts import redirect


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user.username = user.email
        return super().save_user(request, user, form, commit)

    def is_open_for_signup(self, request, sociallogin=None):
        return True

    def pre_signup(self, request, data):
        email = data.get('email')
        if email:
            User = self.get_user_model()
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, "An account with this email already exists. Please login instead.")
                return redirect('account_login')
        return super().pre_signup(request, data)

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        if hasattr(request, 'sociallogin'):
            return

        super().send_confirmation_mail(request, emailconfirmation, signup)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        if sociallogin.user.email:
            try:
                user = sociallogin.user.__class__.objects.get(email=sociallogin.user.email)

                email_address = EmailAddress.objects.filter(user=user, email__iexact=user.email).first()
                if email_address:
                    email_address.verified = True
                    email_address.primary = True
                    email_address.save()

                sociallogin.connect(request, user)
            except sociallogin.user.__class__.DoesNotExist:
                pass

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.username = user.email

        if sociallogin.account.extra_data:
            extra_data = sociallogin.account.extra_data

            # Google returns 'name' field with full name
            if not user.first_name and not user.last_name:
                full_name = extra_data.get('name', '')
                if full_name:
                    name_parts = full_name.split(' ', 1)
                    user.first_name = name_parts[0]
                    if len(name_parts) > 1:
                        user.last_name = name_parts[1]
                else:
                    # Fallback to given_name/family_name if name is not present
                    user.first_name = extra_data.get('given_name', '')
                    user.last_name = extra_data.get('family_name', '')

        email_address, created = EmailAddress.objects.get_or_create(
            user=user,
            email=user.email.lower(),
            defaults={'verified': True, 'primary': True}
        )
        if not created:
            email_address.verified = True
            email_address.primary = True
            email_address.save()

        user.save()
        return user

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.username = user.email

        # Google returns 'name' field with full name
        if not user.first_name and not user.last_name:
            full_name = data.get('name', '')
            if full_name:
                name_parts = full_name.split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
            else:
                # Fallback to given_name/family_name if name is not present
                user.first_name = data.get('given_name', '')
                user.last_name = data.get('family_name', '')

        return user
