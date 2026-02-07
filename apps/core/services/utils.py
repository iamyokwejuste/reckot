from django.conf import settings
from django.templatetags.static import static


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def environment_callback(request):
    if settings.DEBUG:
        return ["Development", "danger"]
    return ["Production", "success"]


def get_logo_path(request):
    return {
        'light': static("images/logo/reckto_logo_dark_mode.png"),
        'dark': static("images/logo/reckto_logo_light_mode.png"),
    }
