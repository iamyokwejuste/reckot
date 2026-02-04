import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SchemaValidator:
    def __init__(self, schema_path: Optional[str | Path] = None):
        if schema_path is None:
            schema_path = (
                Path(__file__).parent.parent.parent.parent
                / "static"
                / "scripts"
                / "data_access_schema.json"
            )

        if isinstance(schema_path, str):
            schema_path = Path(schema_path)

        with open(schema_path, "r") as f:
            self.schema = json.load(f)

        self.tables = self.schema["tables"]
        self.sensitive_keywords = self.schema["sensitive_keywords"]
        self.blocked_operations = self.schema["blocked_operations"]

    def validate_query(
        self, sql: str, access_level: str = "PUBLIC"
    ) -> Tuple[bool, Optional[str], Dict]:
        sql_upper = sql.upper()
        metadata: dict = {
            "tables_accessed": [],
            "columns_accessed": {},
            "sensitive_columns_found": [],
            "blocked_operations_found": [],
        }

        for operation in self.blocked_operations:
            if re.search(rf"\b{operation}\b", sql_upper):
                metadata["blocked_operations_found"].append(operation)
                return False, f"Blocked operation: {operation}", metadata

        tables_in_query = self._extract_tables(sql)
        metadata["tables_accessed"] = list(tables_in_query)

        if not tables_in_query:
            return False, "No tables found in query", metadata

        for table in tables_in_query:
            if table not in self.tables:
                return False, f"Unknown table: {table}", metadata

            table_schema = self.tables[table]
            table_access_level = table_schema["access_level"]

            if table_access_level == "BLOCKED":
                return (
                    False,
                    f"Table '{table}' is not accessible via AI queries",
                    metadata,
                )

            if not self._has_access(access_level, table_access_level):
                return (
                    False,
                    f"Insufficient access level for table '{table}' (requires {table_access_level})",
                    metadata,
                )

        columns_in_query = self._extract_columns(sql)
        metadata["columns_accessed"] = columns_in_query

        for table, columns in columns_in_query.items():
            if table not in self.tables:
                continue

            table_schema = self.tables[table]

            for column in columns:
                if column == "*":
                    return (
                        False,
                        "Wildcard SELECT (*) not allowed. Specify columns explicitly.",
                        metadata,
                    )

                if column not in table_schema["columns"]:
                    return False, f"Unknown column: {table}.{column}", metadata

                column_schema = table_schema["columns"][column]

                if column_schema["sensitive"]:
                    metadata["sensitive_columns_found"].append(f"{table}.{column}")
                    return (
                        False,
                        f"Sensitive column not accessible: {table}.{column}",
                        metadata,
                    )

                column_access = column_schema["access"]
                if column_access == "BLOCKED":
                    return False, f"Column '{table}.{column}' is blocked", metadata

                if not self._has_access(access_level, column_access):
                    return (
                        False,
                        f"Insufficient access for column '{table}.{column}' (requires {column_access})",
                        metadata,
                    )

        for keyword in self.sensitive_keywords:
            if re.search(rf"\b{keyword}\b", sql.lower()):
                metadata["sensitive_columns_found"].append(keyword)
                return False, f"Query contains sensitive keyword: {keyword}", metadata

        for table in tables_in_query:
            table_schema = self.tables[table]
            required_filter = table_schema.get("row_filter")

            if required_filter:
                if "WHERE" not in sql_upper:
                    return (
                        False,
                        f"Table '{table}' requires WHERE clause: {required_filter}",
                        metadata,
                    )

        return True, None, metadata

    def _has_access(self, user_level: str, required_level: str) -> bool:
        hierarchy = ["PUBLIC", "AUTHENTICATED", "ORG_MEMBER", "ADMIN"]

        if required_level == "BLOCKED":
            return False

        try:
            user_idx = hierarchy.index(user_level)
            required_idx = hierarchy.index(required_level)
            return user_idx >= required_idx
        except ValueError:
            return False

    def _extract_tables(self, sql: str) -> Set[str]:
        tables = set()

        from_pattern = r"\bFROM\s+([a-z_][a-z0-9_]*)"
        for match in re.finditer(from_pattern, sql, re.IGNORECASE):
            tables.add(match.group(1).lower())

        join_pattern = r"\bJOIN\s+([a-z_][a-z0-9_]*)"
        for match in re.finditer(join_pattern, sql, re.IGNORECASE):
            tables.add(match.group(1).lower())

        return tables

    def _extract_columns(self, sql: str) -> Dict[str, List[str]]:
        columns: dict = {}

        select_pattern = r"SELECT\s+(.*?)\s+FROM"
        match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

        if match:
            select_clause = match.group(1)

            parts = [p.strip() for p in select_clause.split(",")]

            for part in parts:
                if "." in part:
                    table_col = part.split()[0]
                    if "." in table_col:
                        table, column = table_col.split(".", 1)
                        table = table.lower().strip('`"')
                        column = column.lower().strip('`"')

                        if table not in columns:
                            columns[table] = []
                        columns[table].append(column)

        return columns

    def get_accessible_columns(
        self, table: str, access_level: str = "PUBLIC"
    ) -> List[str]:
        if table not in self.tables:
            return []

        table_schema = self.tables[table]
        accessible = []

        for column, column_schema in table_schema["columns"].items():
            column_access = column_schema["access"]

            if column_access == "BLOCKED":
                continue

            if self._has_access(access_level, column_access):
                accessible.append(column)

        return accessible

    def get_public_tables(self) -> List[str]:
        public_tables = []

        for table, schema in self.tables.items():
            if schema["access_level"] == "PUBLIC":
                public_tables.append(table)

        return public_tables

    def is_column_sensitive(self, table: str, column: str) -> bool:
        if table not in self.tables:
            return True

        table_schema = self.tables[table]

        if column not in table_schema["columns"]:
            return True

        return table_schema["columns"][column]["sensitive"]


if __name__ == "__main__":
    validator = SchemaValidator()

    sql = """
        SELECT id, title, location, start_at
        FROM events_event
        WHERE is_public = TRUE
    """
    is_valid, error, metadata = validator.validate_query(sql, "PUBLIC")
    print(f"Test 1 - Valid public query: {is_valid}")
    if not is_valid:
        print(f"  Error: {error}")
    print(f"  Metadata: {metadata}")

    sql = """
        SELECT id, title, contact_email
        FROM events_event
    """
    is_valid, error, metadata = validator.validate_query(sql, "PUBLIC")
    print(f"\nTest 2 - Sensitive column: {is_valid}")
    if not is_valid:
        print(f"  Error: {error}")
    print(f"  Metadata: {metadata}")

    sql = """
        SELECT COUNT(*) FROM core_user
    """
    is_valid, error, metadata = validator.validate_query(sql, "PUBLIC")
    print(f"\nTest 3 - Blocked table: {is_valid}")
    if not is_valid:
        print(f"  Error: {error}")
    print(f"  Metadata: {metadata}")

    sql = """
        UPDATE events_event SET title = 'Hacked'
    """
    is_valid, error, metadata = validator.validate_query(sql, "PUBLIC")
    print(f"\nTest 4 - Write operation: {is_valid}")
    if not is_valid:
        print(f"  Error: {error}")
    print(f"  Metadata: {metadata}")

    columns = validator.get_accessible_columns("events_event", "PUBLIC")
    print(
        f"\nTest 5 - Accessible columns for events_event (PUBLIC): {len(columns)} columns"
    )
    print(f"  {columns[:5]}...")

    public_tables = validator.get_public_tables()
    print(f"\nTest 6 - Public tables: {public_tables}")
