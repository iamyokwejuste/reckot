import logging
from typing import Any, Dict, List, Optional, Tuple
from django.db import connections
from django.conf import settings
from apps.ai.services.schema_validator import SchemaValidator

logger = logging.getLogger(__name__)


class ReadOnlyQueryExecutor:
    def __init__(self):
        self.validator = SchemaValidator()
        self.db_map = {
            "PUBLIC": "ai_public_readonly",
            "AUTHENTICATED": "ai_auth_readonly",
            "ORG_MEMBER": "ai_org_readonly",
        }
        self._validate_database_engine()

    def _validate_database_engine(self):
        default_engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
        if "postgresql" not in default_engine:
            logger.error(
                f"RBAC queries require PostgreSQL. Current engine: {default_engine}. "
                "SQLite does not support user-based authentication."
            )
            raise RuntimeError(
                "AI queries with RBAC are only supported with PostgreSQL. "
                "Please configure PostgreSQL in your settings or disable AI query features."
            )

    def execute_query(
        self,
        sql: str,
        access_level: str = "PUBLIC",
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        is_valid, error, metadata = self.validator.validate_query(sql, access_level)

        if not is_valid:
            logger.warning(f"Query validation failed: {error}")
            return {
                "success": False,
                "error": error,
                "metadata": metadata,
                "data": None,
            }

        db_alias = self.db_map.get(access_level, "ai_public_readonly")

        db_config = settings.DATABASES.get(db_alias)
        if not db_config:
            logger.error(f"Database alias '{db_alias}' not configured in settings")
            return {
                "success": False,
                "error": f"Database configuration missing for access level: {access_level}",
                "metadata": metadata,
                "data": None,
            }

        db_user = db_config.get("USER", "")
        if not db_user or db_user == settings.DATABASES["default"].get("USER"):
            logger.error(
                f"RBAC user not properly configured. "
                f"Database '{db_alias}' should use a different user than default."
            )
            return {
                "success": False,
                "error": "RBAC database users not configured. Please set up read-only database users.",
                "metadata": metadata,
                "data": None,
            }

        try:
            with connections[db_alias].cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                if sql.strip().upper().startswith("SELECT"):
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()

                    data = [dict(zip(columns, row)) for row in rows]

                    return {
                        "success": True,
                        "data": data,
                        "columns": columns,
                        "row_count": len(data),
                        "metadata": metadata,
                    }
                else:
                    return {
                        "success": False,
                        "error": "Only SELECT queries are allowed",
                        "metadata": metadata,
                        "data": None,
                    }

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return {
                "success": False,
                "error": f"Query execution error: {str(e)}",
                "metadata": metadata,
                "data": None,
            }

    def execute_ai_query(
        self,
        user_question: str,
        sql: str,
        access_level: str = "PUBLIC",
        user_id: Optional[int] = None,
        org_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        params = {}

        if access_level == "AUTHENTICATED" and user_id:
            params["current_user_id"] = user_id

        if access_level == "ORG_MEMBER" and org_ids:
            params["user_org_ids"] = tuple(org_ids)

        result = self.execute_query(sql, access_level, params)

        if result["success"]:
            logger.info(f"AI query executed successfully: {user_question}")
        else:
            logger.warning(f"AI query failed: {user_question} - {result['error']}")

        return result

    def get_table_preview(
        self, table: str, access_level: str = "PUBLIC", limit: int = 10
    ) -> Dict[str, Any]:
        if table not in self.validator.tables:
            return {"success": False, "error": f"Unknown table: {table}", "data": None}

        accessible_columns = self.validator.get_accessible_columns(table, access_level)

        if not accessible_columns:
            return {
                "success": False,
                "error": f"No accessible columns for table: {table}",
                "data": None,
            }

        columns_str = ", ".join(accessible_columns)
        sql = f"SELECT {columns_str} FROM {table} LIMIT {limit}"

        return self.execute_query(sql, access_level)

    def validate_and_execute(
        self, sql: str, access_level: str = "PUBLIC"
    ) -> Tuple[bool, Optional[str], Optional[List[Dict]]]:
        result = self.execute_query(sql, access_level)

        if result["success"]:
            return True, None, result["data"]
        else:
            return False, result["error"], None
