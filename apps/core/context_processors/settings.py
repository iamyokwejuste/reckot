from django.conf import settings


def cache_version(request):
    return {
        'CACHE_VERSION': settings.CACHE_VERSION,
    }
