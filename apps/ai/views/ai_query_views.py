import json
import logging
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.ai.services import AIQueryService, SchemaValidator
from apps.ai.utils.decorators import ai_rate_limit

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class AIQueryPublicView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            question = data.get("question")

            if not question:
                return JsonResponse(
                    {"success": False, "error": "Question is required"}, status=400
                )

            service = AIQueryService()
            result = service.answer_question(question, user=None)

            return JsonResponse(result)

        except Exception as e:
            logger.error(f"Public AI query failed: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)


@method_decorator(ai_rate_limit, name="dispatch")
class AIQueryAuthenticatedView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            question = data.get("question")

            if not question:
                return JsonResponse(
                    {"success": False, "error": "Question is required"}, status=400
                )

            service = AIQueryService()
            result = service.answer_question(question, user=request.user)

            return JsonResponse(result)

        except Exception as e:
            logger.error(f"Authenticated AI query failed: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class AIQueryValidateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            sql = data.get("sql")
            access_level = data.get("access_level", "PUBLIC")

            if not sql:
                return JsonResponse(
                    {"success": False, "error": "SQL is required"}, status=400
                )

            validator = SchemaValidator()
            is_valid, error, metadata = validator.validate_query(sql, access_level)

            return JsonResponse(
                {"valid": is_valid, "error": error, "metadata": metadata}
            )

        except Exception as e:
            logger.error(f"SQL validation failed: {str(e)}")
            return JsonResponse({"valid": False, "error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class AIGenerateSQLView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            question = data.get("question")
            access_level = data.get("access_level", "PUBLIC")

            if not question:
                return JsonResponse(
                    {"success": False, "error": "Question is required"}, status=400
                )

            service = AIQueryService()
            result = service.generate_sql(question, access_level)

            return JsonResponse(result)

        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class AISchemaInfoView(View):
    def get(self, request):
        try:
            validator = SchemaValidator()

            access_level = request.GET.get("access_level", "PUBLIC")

            accessible_tables = {}
            for table_name, table_schema in validator.tables.items():
                if validator._has_access(access_level, table_schema["access_level"]):
                    columns = validator.get_accessible_columns(table_name, access_level)
                    if columns:
                        accessible_tables[table_name] = {
                            "columns": columns,
                            "description": table_schema.get("description", ""),
                            "access_level": table_schema["access_level"],
                            "row_filter": table_schema.get("row_filter"),
                        }

            return JsonResponse(
                {
                    "access_level": access_level,
                    "tables": accessible_tables,
                    "table_count": len(accessible_tables),
                }
            )

        except Exception as e:
            logger.error(f"Schema info failed: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
