from django.conf import settings
from django.http import HttpResponseForbidden


class AdminOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_only_mode = getattr(settings, 'ADMIN_ONLY_MODE', False)

    def __call__(self, request):
        if self.admin_only_mode:
            path = request.path
            allowed_paths = [
                '/admin/',
                '/health/',
                '/static/',
                '/media/',
            ]

            if not any(path.startswith(allowed_path) for allowed_path in allowed_paths):
                return HttpResponseForbidden('This service only serves admin interface')

        response = self.get_response(request)
        return response
