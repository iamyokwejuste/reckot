from django.conf import settings


def platform_settings(request):
    return {
        'PLATFORM_FEE_PERCENTAGE': int(getattr(settings, 'RECKOT_PLATFORM_FEE_PERCENTAGE', 7)),
    }
