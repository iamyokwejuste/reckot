from django.conf import settings
from django.http import HttpResponseRedirect


class AdminRootRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_only_mode = getattr(settings, 'ADMIN_ONLY_MODE', False)

    def __call__(self, request):
        if self.admin_only_mode and request.path == '/':
            return HttpResponseRedirect('/admin/')

        response = self.get_response(request)
        return response
