import json
import logging
from typing import Any, Dict, List, Optional
from django.conf import settings
from google import genai
from apps.ai.services.query_executor import ReadOnlyQueryExecutor
from apps.ai.services.schema_validator import SchemaValidator

logger = logging.getLogger(__name__)


class AIQueryService:
    def __init__(self):
        self.executor = ReadOnlyQueryExecutor()
        self.validator = SchemaValidator()
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_LITE_MODEL
        self._client = None
        if self.api_key:
            self._client = genai.Client(api_key=self.api_key)

    def get_user_access_level(self, user) -> str:
        if not user or not user.is_authenticated:
            return 'PUBLIC'

        from apps.orgs.models import Membership
        if Membership.objects.filter(user=user).exists():
            return 'ORG_MEMBER'

        return 'AUTHENTICATED'

    def get_user_org_ids(self, user) -> List[int]:
        if not user or not user.is_authenticated:
            return []

        from apps.orgs.models import Membership
        return list(
            Membership.objects.filter(user=user)
            .values_list('organization_id', flat=True)
        )

    def generate_sql(
        self,
        user_question: str,
        access_level: str = 'PUBLIC'
    ) -> Dict[str, Any]:
        accessible_tables = {}

        for table_name, table_schema in self.validator.tables.items():
            if self.validator._has_access(access_level, table_schema['access_level']):
                columns = self.validator.get_accessible_columns(table_name, access_level)
                if columns:
                    accessible_tables[table_name] = {
                        'columns': columns,
                        'description': table_schema.get('description', ''),
                        'row_filter': table_schema.get('row_filter')
                    }

        schema_context = json.dumps(accessible_tables, indent=2)

        prompt = f"""You are a SQL query generator for a Django event management platform.

User Access Level: {access_level}

Available Database Schema:
{schema_context}

CRITICAL RULES:
1. ONLY use tables and columns listed above
2. NEVER use SELECT * - always specify columns explicitly
3. NEVER use INSERT, UPDATE, DELETE, DROP or any write operations
4. ALWAYS include required WHERE clauses shown in row_filter
5. For PUBLIC access, only query public published events
6. Return ONLY valid PostgreSQL SELECT statement, no explanations

User Question: {user_question}

Generate SQL query:"""

        try:
            if not self._client:
                return {
                    'success': False,
                    'error': 'AI service not available. Please configure GEMINI_API_KEY.',
                    'sql': None
                }

            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={'max_output_tokens': 512, 'temperature': 0.3}
            )
            sql = response.text.strip()

            sql = sql.replace('```sql', '').replace('```', '').strip()

            if not sql.upper().startswith('SELECT'):
                return {
                    'success': False,
                    'error': 'Generated query is not a SELECT statement',
                    'sql': sql
                }

            return {
                'success': True,
                'sql': sql,
                'schema_used': list(accessible_tables.keys())
            }

        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to generate SQL: {str(e)}",
                'sql': None
            }

    def answer_question(
        self,
        user_question: str,
        user=None
    ) -> Dict[str, Any]:
        access_level = self.get_user_access_level(user)
        user_id = user.id if user and user.is_authenticated else None
        org_ids = self.get_user_org_ids(user)

        sql_result = self.generate_sql(user_question, access_level)

        if not sql_result['success']:
            return {
                'success': False,
                'question': user_question,
                'error': sql_result['error'],
                'data': None,
                'sql': None
            }

        sql = sql_result['sql']

        execution_result = self.executor.execute_ai_query(
            user_question=user_question,
            sql=sql,
            access_level=access_level,
            user_id=user_id,
            org_ids=org_ids
        )

        return {
            'success': execution_result['success'],
            'question': user_question,
            'sql': sql,
            'data': execution_result.get('data'),
            'row_count': execution_result.get('row_count', 0),
            'error': execution_result.get('error'),
            'access_level': access_level,
            'metadata': execution_result.get('metadata')
        }

    def execute_raw_sql(
        self,
        sql: str,
        access_level: str = 'PUBLIC',
        user_id: Optional[int] = None,
        org_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        return self.executor.execute_ai_query(
            user_question='Direct SQL execution',
            sql=sql,
            access_level=access_level,
            user_id=user_id,
            org_ids=org_ids
        )
