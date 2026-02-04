import time
import json
import re
from functools import wraps
from datetime import date
from typing import Callable, Any
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db.models import F
from apps.ai.models import AIRateLimit, AIUsageLog


def ai_feature_required(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    def wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return JsonResponse(
                {
                    "error": "Please log in to use AI features.",
                    "disabled": True,
                },
                status=403,
            )

        if not request.user.ai_features_enabled:
            return JsonResponse(
                {
                    "error": "AI features disabled. Enable in settings.",
                    "disabled": True,
                },
                status=403,
            )
        return view_func(request, *args, **kwargs)

    return wrapped_view


def ai_rate_limit(
    limit: int = 30,
) -> Callable[[Callable[..., HttpResponse]], Callable[..., HttpResponse]]:
    def decorator(
        view_func: Callable[..., HttpResponse],
    ) -> Callable[..., HttpResponse]:
        @wraps(view_func)
        def wrapped_view(
            request: HttpRequest, *args: Any, **kwargs: Any
        ) -> HttpResponse:
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)

            today = date.today()
            rate_limit, created = AIRateLimit.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={"request_count": 0, "daily_limit": limit},
            )

            if rate_limit.request_count >= rate_limit.daily_limit:
                return JsonResponse(
                    {
                        "error": f"Daily AI limit reached ({limit}/day). Try tomorrow.",
                        "limit_reached": True,
                    },
                    status=429,
                )

            AIRateLimit.objects.filter(id=rate_limit.id).update(
                request_count=F("request_count") + 1
            )

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def log_ai_usage(
    operation: str,
) -> Callable[[Callable[..., HttpResponse]], Callable[..., HttpResponse]]:
    def decorator(
        view_func: Callable[..., HttpResponse],
    ) -> Callable[..., HttpResponse]:
        @wraps(view_func)
        def wrapped_view(
            request: HttpRequest, *args: Any, **kwargs: Any
        ) -> HttpResponse:
            start_time = time.time()
            error = ""

            try:
                response = view_func(request, *args, **kwargs)
                return response
            except Exception as e:
                error = str(e)
                raise
            finally:
                execution_time = time.time() - start_time
                prompt = ""

                if hasattr(request, "body"):
                    try:
                        data = json.loads(request.body)
                        prompt = (
                            data.get("message", "")
                            or data.get("prompt", "")
                            or data.get("text", "")
                        )
                    except (json.JSONDecodeError, ValueError):
                        pass

                AIUsageLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    operation=operation,
                    prompt=prompt[:1000],
                    execution_time=execution_time,
                    error=error,
                    ip_address=request.META.get("REMOTE_ADDR"),
                )

        return wrapped_view

    return decorator


def validate_query(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    ALLOWED_MODELS = [
        "Event",
        "Ticket",
        "Payment",
        "Organization",
        "Booking",
        "TicketType",
    ]
    FORBIDDEN_PATTERNS = [
        r"\.delete\(",
        r"\.update\(",
        r"\.create\(",
        r"\.save\(",
        r"\.bulk_create\(",
        r"\.bulk_update\(",
        r"\.raw\(",
        r"\.execute\(",
        r"__import__",
        r"eval\(",
        r"exec\(",
        r"compile\(",
        r"globals\(",
        r"locals\(",
        r"vars\(",
        r"__",
    ]

    @wraps(view_func)
    def wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = view_func(request, *args, **kwargs)

        if hasattr(response, "content"):
            try:
                data = json.loads(response.content)

                if data.get("action") == "execute_query":
                    if "query_result" in data:
                        return response

                    query = data.get("query", "").strip()

                    if not query:
                        return JsonResponse(
                            {
                                "error": "Query blocked: empty query",
                                "query_blocked": True,
                            },
                            status=403,
                        )

                    for pattern in FORBIDDEN_PATTERNS:
                        if re.search(pattern, query, re.IGNORECASE):
                            return JsonResponse(
                                {
                                    "error": "Query blocked: forbidden operations detected",
                                    "query_blocked": True,
                                },
                                status=403,
                            )

                    model_pattern = r"\b(" + "|".join(ALLOWED_MODELS) + r")\.objects\b"
                    if not re.search(model_pattern, query):
                        return JsonResponse(
                            {
                                "error": "Query blocked: no authorized model found",
                                "query_blocked": True,
                            },
                            status=403,
                        )

                    if len(query) > 2000:
                        return JsonResponse(
                            {
                                "error": "Query blocked: query too long",
                                "query_blocked": True,
                            },
                            status=403,
                        )

            except (json.JSONDecodeError, ValueError, KeyError):
                pass

        return response

    return wrapped_view
