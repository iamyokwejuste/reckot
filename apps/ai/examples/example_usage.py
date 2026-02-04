from apps.ai.services import AIQueryService, ReadOnlyQueryExecutor, SchemaValidator


def example_1_direct_sql():
    print("="*60)
    print("Example 1: Direct SQL Execution with Validation")
    print("="*60)

    executor = ReadOnlyQueryExecutor()

    sql = """
        SELECT id, title, location, city, start_at
        FROM events_event
        WHERE is_public = TRUE AND state = 'PUBLISHED'
        LIMIT 5
    """

    result = executor.execute_query(sql, access_level='PUBLIC')

    if result['success']:
        print("✓ Query executed successfully")
        print(f"  Rows returned: {result['row_count']}")
        print(f"  Columns: {', '.join(result['columns'])}")
        print(f"\n  First row: {result['data'][0] if result['data'] else 'No data'}")
    else:
        print(f"✗ Query failed: {result['error']}")

    print()


def example_2_ai_question():
    print("="*60)
    print("Example 2: AI Natural Language Query")
    print("="*60)

    service = AIQueryService()

    question = "How many public events are scheduled in Paris?"

    print(f"Question: {question}")
    print()

    result = service.answer_question(question, user=None)

    if result['success']:
        print("✓ Query successful")
        print(f"  Generated SQL: {result['sql']}")
        print(f"  Result: {result['data']}")
        print(f"  Access Level: {result['access_level']}")
    else:
        print(f"✗ Query failed: {result['error']}")

    print()


def example_3_validation():
    print("="*60)
    print("Example 3: Query Validation")
    print("="*60)

    validator = SchemaValidator()

    test_queries = [
        ("Valid public query", "SELECT id, title FROM events_event WHERE is_public = TRUE"),
        ("Blocked sensitive column", "SELECT contact_email FROM events_event"),
        ("Blocked table", "SELECT email FROM core_user"),
        ("Write operation", "UPDATE events_event SET title = 'Test'"),
        ("Wildcard select", "SELECT * FROM events_event"),
    ]

    for name, sql in test_queries:
        is_valid, error, metadata = validator.validate_query(sql, 'PUBLIC')
        status = "✓ ALLOWED" if is_valid else "✗ BLOCKED"
        print(f"{status}: {name}")
        if not is_valid:
            print(f"         Reason: {error}")
        print()


def example_4_accessible_schema():
    print("="*60)
    print("Example 4: View Accessible Schema")
    print("="*60)

    validator = SchemaValidator()

    public_tables = validator.get_public_tables()

    print(f"Public tables ({len(public_tables)}):")
    for table in public_tables:
        columns = validator.get_accessible_columns(table, 'PUBLIC')
        print(f"\n  {table}")
        print(f"    Columns: {', '.join(columns[:5])}...")
        print(f"    Total accessible columns: {len(columns)}")

    print()


def example_5_table_preview():
    print("="*60)
    print("Example 5: Table Preview")
    print("="*60)

    executor = ReadOnlyQueryExecutor()

    result = executor.get_table_preview('events_event', access_level='PUBLIC', limit=3)

    if result['success']:
        print("✓ Preview successful")
        print(f"  Rows: {len(result['data'])}")
        for i, row in enumerate(result['data'], 1):
            print(f"\n  Row {i}:")
            for key, value in list(row.items())[:3]:
                print(f"    {key}: {value}")
    else:
        print(f"✗ Preview failed: {result['error']}")

    print()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("AI GOVERNANCE - READ-ONLY QUERY EXAMPLES")
    print("="*60 + "\n")

    example_1_direct_sql()
    example_2_ai_question()
    example_3_validation()
    example_4_accessible_schema()
    example_5_table_preview()

    print("="*60)
    print("All examples completed")
    print("="*60)
