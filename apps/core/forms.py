from django import forms
from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "+237 6XX XXX XXX",
                "class": "input",
                "autocomplete": "tel",
            }
        ),
    )

    def save(self, request):
        user = super().save(request)
        user.phone_number = self.cleaned_data.get("phone_number")
        if user.phone_number:
            user.save(update_fields=["phone_number"])
        return user
