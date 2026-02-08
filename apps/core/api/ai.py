import json
import base64
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from apps.core.services.ai import gemini_ai


@require_POST
@csrf_protect
@login_required
def generate_description(request):
    try:
        data = json.loads(request.body)
        title = data.get("title", "")
        bullet_points = data.get("bullet_points", "")
        event_type = data.get("event_type", "general")
        short_description = data.get("short_description", "")
        location = data.get("location", "")
        cover_image_base64 = data.get("cover_image", "")
        cover_image_mime = data.get("cover_image_mime", "image/jpeg")

        if not title:
            return JsonResponse({"error": _("Title is required.")}, status=400)

        cover_image_data = None
        if cover_image_base64:
            try:
                if "," in cover_image_base64:
                    cover_image_base64 = cover_image_base64.split(",")[1]
                cover_image_data = base64.b64decode(cover_image_base64)
            except Exception:
                pass

        if cover_image_data or short_description or location:
            result = gemini_ai.generate_from_event_context(
                title=title,
                short_description=short_description,
                event_type=event_type,
                location=location,
                cover_image_data=cover_image_data,
                cover_image_mime=cover_image_mime,
            )
        elif bullet_points:
            result = gemini_ai.generate_event_description(
                title, bullet_points, event_type
            )
        else:
            result = gemini_ai.generate_from_event_context(
                title=title, event_type=event_type
            )

        if result:
            if isinstance(result, dict):
                return JsonResponse(
                    {
                        "tagline": result.get("tagline", ""),
                        "description": result.get("description", ""),
                    }
                )
            return JsonResponse({"description": result, "tagline": ""})
        return JsonResponse(
            {"error": _("Failed to generate description. Check API key.")}, status=500
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
def improve_description(request):
    try:
        data = json.loads(request.body)
        description = data.get("description", "")

        if not description:
            return JsonResponse({"error": _("Description is required.")}, status=400)

        result = gemini_ai.improve_description(description)

        if result:
            return JsonResponse({"description": result})
        return JsonResponse({"error": _("Failed to improve description")}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
def generate_seo(request):
    try:
        data = json.loads(request.body)
        title = data.get("title", "")
        description = data.get("description", "")

        if not title:
            return JsonResponse({"error": _("Title is required.")}, status=400)

        result = gemini_ai.generate_seo_meta(title, description)

        if result:
            return JsonResponse(result)
        return JsonResponse({"error": _("Failed to generate SEO metadata")}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
def generate_social_caption(request):
    try:
        data = json.loads(request.body)
        title = data.get("title", "")
        description = data.get("description", "")
        platform = data.get("platform", "general")

        if not title:
            return JsonResponse({"error": _("Title is required.")}, status=400)

        result = gemini_ai.generate_social_caption(title, description, platform)

        if result:
            return JsonResponse({"caption": result})
        return JsonResponse({"error": _("Failed to generate caption")}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
def translate_text(request):
    try:
        data = json.loads(request.body)
        text = data.get("text", "")
        target_language = data.get("language", "French")

        if not text:
            return JsonResponse({"error": _("Text is required.")}, status=400)

        result = gemini_ai.translate_text(text, target_language)

        if result:
            return JsonResponse({"translation": result})
        return JsonResponse({"error": _("Failed to translate")}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
def summarize_text(request):
    try:
        data = json.loads(request.body)
        text = data.get("text", "")
        max_words = data.get("max_words", 30)

        if not text:
            return JsonResponse({"error": _("Text is required.")}, status=400)

        result = gemini_ai.summarize_description(text, max_words)

        if result:
            return JsonResponse({"summary": result})
        return JsonResponse({"error": _("Failed to summarize")}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
def suggest_pricing(request):
    try:
        data = json.loads(request.body)
        event_type = data.get("event_type", "general")
        location = data.get("location", "Cameroon")
        description = data.get("description", "")

        result = gemini_ai.suggest_ticket_pricing(event_type, location, description)

        if result:
            return JsonResponse(result)
        return JsonResponse({"error": _("Failed to suggest pricing")}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
def suggest_tags(request):
    try:
        data = json.loads(request.body)
        title = data.get("title", "")
        description = data.get("description", "")

        if not title:
            return JsonResponse({"error": _("Title is required.")}, status=400)

        result = gemini_ai.suggest_event_tags(title, description)

        if result:
            return JsonResponse({"tags": result})
        return JsonResponse({"error": _("Failed to suggest tags")}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
def event_assistant(request):
    try:
        data = json.loads(request.body)
        event_info = data.get("event_info", {})
        question = data.get("question", "")

        if not question:
            return JsonResponse({"error": _("Question is required.")}, status=400)

        result = gemini_ai.answer_event_question(event_info, question)

        if result:
            return JsonResponse({"answer": result})
        return JsonResponse({"error": _("Failed to get answer")}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_protect
@login_required
def generate_insight(request):
    try:
        data = json.loads(request.body)
        metrics = data.get("metrics", {})

        if not metrics:
            return JsonResponse({"error": _("Metrics are required.")}, status=400)

        result = gemini_ai.generate_analytics_insight(metrics)

        if result:
            return JsonResponse({"insight": result})
        return JsonResponse({"error": _("Failed to generate insight")}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
