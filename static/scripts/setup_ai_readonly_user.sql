DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'reckot_ai_public_readonly') THEN
        CREATE USER reckot_ai_public_readonly WITH PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'reckot_ai_auth_readonly') THEN
        CREATE USER reckot_ai_auth_readonly WITH PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'reckot_ai_org_readonly') THEN
        CREATE USER reckot_ai_org_readonly WITH PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE reckot TO reckot_ai_public_readonly;
GRANT CONNECT ON DATABASE reckot TO reckot_ai_auth_readonly;
GRANT CONNECT ON DATABASE reckot TO reckot_ai_org_readonly;

GRANT USAGE ON SCHEMA public TO reckot_ai_public_readonly;
GRANT USAGE ON SCHEMA public TO reckot_ai_auth_readonly;
GRANT USAGE ON SCHEMA public TO reckot_ai_org_readonly;

GRANT SELECT (
    id, organization_id, category_id, title, description, short_description,
    cover_image, location, venue_name, city, country, start_at, end_at,
    timezone, event_type, capacity, is_public, state, is_free, created_at
) ON events_event TO reckot_ai_public_readonly;

GRANT SELECT (
    id, name, slug, description, icon, color, is_active, display_order
) ON events_eventcategory TO reckot_ai_public_readonly;

GRANT SELECT (
    id, event_id, name, price, description, quantity, sales_start, sales_end, is_active
) ON tickets_tickettype TO reckot_ai_public_readonly;

GRANT SELECT (
    id, name, slug, description, logo, website
) ON orgs_organization TO reckot_ai_public_readonly;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM reckot_ai_public_readonly;

REVOKE ALL PRIVILEGES ON core_user FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON tickets_booking FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON tickets_ticket FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON payments_payment FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON payments_paymentgatewayconfig FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON payments_offlinepayment FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON payments_withdrawal FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON core_otpverification FROM reckot_ai_public_readonly;
REVOKE ALL PRIVILEGES ON auth_user FROM reckot_ai_public_readonly;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM reckot_ai_public_readonly;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM reckot_ai_auth_readonly;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM reckot_ai_org_readonly;

REVOKE CREATE ON SCHEMA public FROM reckot_ai_public_readonly;
REVOKE CREATE ON SCHEMA public FROM reckot_ai_auth_readonly;
REVOKE CREATE ON SCHEMA public FROM reckot_ai_org_readonly;

REVOKE UPDATE ON ALL SEQUENCES IN SCHEMA public FROM reckot_ai_public_readonly;
REVOKE UPDATE ON ALL SEQUENCES IN SCHEMA public FROM reckot_ai_auth_readonly;
REVOKE UPDATE ON ALL SEQUENCES IN SCHEMA public FROM reckot_ai_org_readonly;

ALTER TABLE events_event ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ai_public_events_policy ON events_event;
CREATE POLICY ai_public_events_policy ON events_event
    FOR SELECT TO reckot_ai_public_readonly
    USING (is_public = TRUE AND state = 'PUBLISHED' AND start_at > NOW() - INTERVAL '30 days');

ALTER TABLE tickets_tickettype ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ai_public_tickettypes_policy ON tickets_tickettype;
CREATE POLICY ai_public_tickettypes_policy ON tickets_tickettype
    FOR SELECT TO reckot_ai_public_readonly
    USING (event_id IN (SELECT id FROM events_event WHERE is_public = TRUE AND state = 'PUBLISHED'));

ALTER USER reckot_ai_public_readonly CONNECTION LIMIT 10;
ALTER USER reckot_ai_auth_readonly CONNECTION LIMIT 20;
ALTER USER reckot_ai_org_readonly CONNECTION LIMIT 50;

DO $$
DECLARE
    test_result RECORD;
BEGIN
    SET ROLE reckot_ai_public_readonly;
    SELECT COUNT(*) as event_count INTO test_result FROM events_event WHERE is_public = TRUE;
    RAISE NOTICE 'Test 1 PASSED: Can read % public events', test_result.event_count;
    RESET ROLE;
EXCEPTION
    WHEN OTHERS THEN
        RESET ROLE;
        RAISE NOTICE 'Test 1 FAILED: %', SQLERRM;
END $$;

DO $$
BEGIN
    SET ROLE reckot_ai_public_readonly;
    PERFORM email FROM core_user LIMIT 1;
    RESET ROLE;
    RAISE NOTICE 'Test 2 FAILED: Should not be able to read user emails!';
EXCEPTION
    WHEN insufficient_privilege THEN
        RESET ROLE;
        RAISE NOTICE 'Test 2 PASSED: Correctly blocked access to sensitive user data';
    WHEN OTHERS THEN
        RESET ROLE;
        RAISE NOTICE 'Test 2 ERROR: %', SQLERRM;
END $$;

DO $$
BEGIN
    SET ROLE reckot_ai_public_readonly;
    UPDATE events_event SET title = 'Hacked' WHERE id = 1;
    RESET ROLE;
    RAISE NOTICE 'Test 3 FAILED: Should not be able to update events!';
EXCEPTION
    WHEN insufficient_privilege THEN
        RESET ROLE;
        RAISE NOTICE 'Test 3 PASSED: Correctly blocked UPDATE operation';
    WHEN OTHERS THEN
        RESET ROLE;
        RAISE NOTICE 'Test 3 ERROR: %', SQLERRM;
END $$;

GRANT SELECT (
    id, organization_id, category_id, title, description, short_description,
    cover_image, location, venue_name, city, country, start_at, end_at,
    timezone, event_type, capacity, is_public, state, is_free, created_at
) ON events_event TO reckot_ai_auth_readonly;

GRANT SELECT (
    id, name, slug, description, icon, color, is_active, display_order
) ON events_eventcategory TO reckot_ai_auth_readonly;

GRANT SELECT (
    id, event_id, name, price, description, quantity, sales_start, sales_end, is_active
) ON tickets_tickettype TO reckot_ai_auth_readonly;

GRANT SELECT (
    id, name, slug, description, logo, website
) ON orgs_organization TO reckot_ai_auth_readonly;

GRANT SELECT (
    id, organization_id, category_id, title, description, short_description,
    cover_image, location, venue_name, city, country, start_at, end_at,
    timezone, event_type, capacity, is_public, state, is_free,
    contact_email, contact_phone, created_at
) ON events_event TO reckot_ai_org_readonly;

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'AI Read-Only User Setup Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Created users:';
    RAISE NOTICE '  - reckot_ai_public_readonly (PUBLIC access)';
    RAISE NOTICE '  - reckot_ai_auth_readonly (AUTHENTICATED access)';
    RAISE NOTICE '  - reckot_ai_org_readonly (ORG_MEMBER access)';
    RAISE NOTICE '';
    RAISE NOTICE 'Permissions granted:';
    RAISE NOTICE '  - SELECT on non-sensitive columns only';
    RAISE NOTICE '  - Row-level security enabled';
    RAISE NOTICE '  - ALL write operations blocked';
    RAISE NOTICE '';
    RAISE NOTICE 'IMPORTANT: Change default passwords!';
    RAISE NOTICE '  ALTER USER reckot_ai_public_readonly PASSWORD ''new_secure_password'';';
    RAISE NOTICE '';
END $$;
