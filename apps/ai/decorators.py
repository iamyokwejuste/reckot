import time
import json
from functools import wraps
from datetime import date
from django.http import JsonResponse
from django.db.models import F
from apps.ai.models import AIRateLimit, AIUsageLog


def ai_feature_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.ai_features_enabled:
            return JsonResponse(
                {
                    "error": "AI features disabled. Enable in settings.",
                    "disabled": True,
                },
                status=403,
            )
        return view_func(request, *args, **kwargs)

    return wrapped_view


def ai_rate_limit(limit=30):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
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


def log_ai_usage(operation):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
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


def validate_query(view_func):
    ALLOWED_MODELS = ["Event", "Ticket", "Payment", "Organization", "Booking"]
    FORBIDDEN_METHODS = [
        "delete",
        "update",
        "create",
        "save",
        "bulk_create",
        "bulk_update",
    ]

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)

        if hasattr(response, "content"):
            try:
                data = json.loads(response.content)

                if data.get("action") == "execute_query":
                    query = data.get("query", "")

                    for method in FORBIDDEN_METHODS:
                        if f".{method}(" in query:
                            return JsonResponse(
                                {
                                    "error": "Query blocked: forbidden operations",
                                    "query_blocked": True,
                                },
                                status=403,
                            )

                    model_found = False
                    for model in ALLOWED_MODELS:
                        if query.startswith(f"{model}.objects"):
                            model_found = True
                            break

                    if not model_found:
                        return JsonResponse(
                            {
                                "error": "Query blocked: unauthorized model",
                                "query_blocked": True,
                            },
                            status=403,
                        )

            except (json.JSONDecodeError, ValueError, KeyError):
                pass

        return response

    return wrapped_view
