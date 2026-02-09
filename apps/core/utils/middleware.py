import time
import hashlib
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, "RATE_LIMITING_ENABLED", True)

    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)

        exempt_paths = ["/admin/", "/static/", "/health/", "/i18n/"]
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        client_ip = self.get_client_ip(request)
        user_id = str(request.user.id) if request.user.is_authenticated else None

        rate_key = user_id or client_ip
        path_prefix = self.get_path_prefix(request.path)

        if path_prefix == "api":
            limit, window = 100, 60
        elif path_prefix == "export":
            limit, window = 10, 3600
        elif path_prefix == "withdrawal":
            limit, window = 5, 86400
        elif path_prefix == "webhook":
            limit, window = 50, 60
        else:
            limit, window = 200, 60

        cache_key = f"ratelimit:{path_prefix}:{rate_key}"
        current_count = cache.get(cache_key, 0)

        if current_count >= limit:
            return JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "limit": limit,
                    "window": window,
                    "retry_after": self.get_retry_after(cache_key, window),
                },
                status=429,
            )

        cache.set(cache_key, current_count + 1, window)

        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(max(0, limit - current_count - 1))
        response["X-RateLimit-Reset"] = str(int(time.time()) + window)

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def get_path_prefix(self, path):
        if "/api/" in path:
            return "api"
        elif "/reports/export" in path or "/export" in path:
            return "export"
        elif "/withdrawal" in path:
            return "withdrawal"
        elif "/webhook" in path:
            return "webhook"
        return "general"

    def get_retry_after(self, cache_key, window):
        ttl = cache.ttl(cache_key)
        return ttl if ttl and ttl > 0 else window


class ModeAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        mode_access = getattr(settings, "MODE_ACCESS", {})
        self.organizer_paths = mode_access.get("ORGANIZER_PATHS", [])
        self.organizer_event_suffixes = mode_access.get("ORGANIZER_EVENT_SUFFIXES", [])
        self.organizer_event_prefixes = mode_access.get("ORGANIZER_EVENT_PREFIXES", [])
        self.speaker_paths = mode_access.get("SPEAKER_PATHS", [])
        self.exempt_paths = mode_access.get("EXEMPT_PATHS", [])

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        if any(path.startswith(p) for p in self.exempt_paths):
            return self.get_response(request)

        mode = getattr(request.user, "active_mode", "ATTENDEE")

        if mode != "ORGANIZER":
            if any(path.startswith(p) for p in self.organizer_paths):
                return self._deny(request, "ORGANIZER")

            if any(path.startswith(p) for p in self.organizer_event_prefixes):
                return self._deny(request, "ORGANIZER")

            if path.startswith("/events/") and not path.startswith("/events/discover"):
                for suffix in self.organizer_event_suffixes:
                    if path.endswith(suffix) or suffix[:-1] + "/" in path:
                        return self._deny(request, "ORGANIZER")

        if mode != "SPEAKER":
            if any(path.startswith(p) for p in self.speaker_paths):
                return self._deny(request, "SPEAKER")

        return self.get_response(request)

    def _deny(self, request, required_mode):
        mode_labels = {
            "ORGANIZER": _("Organizer"),
            "SPEAKER": _("Speaker"),
            "ATTENDEE": _("Attendee"),
        }
        required_label = mode_labels.get(required_mode, required_mode)
        return render(
            request,
            "errors/mode_required.html",
            {
                "required_mode": required_mode,
                "required_label": required_label,
                "current_mode": getattr(request.user, "active_mode", "ATTENDEE"),
            },
            status=403,
        )
