DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'reckot_ai_public_readonly') THEN
        CREATE USER reckot_ai_public_readonly WITH PASSWORD :'AI_PUBLIC_READONLY_PASSWORD';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'reckot_ai_auth_readonly') THEN
        CREATE USER reckot_ai_auth_readonly WITH PASSWORD :'AI_AUTH_READONLY_PASSWORD';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'reckot_ai_org_readonly') THEN
        CREATE USER reckot_ai_org_readonly WITH PASSWORD :'AI_ORG_READONLY_PASSWORD';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE reckot TO reckot_ai_public_readonly;
GRANT CONNECT ON DATABASE reckot TO reckot_ai_auth_readonly;
GRANT CONNECT ON DATABASE reckot TO reckot_ai_org_readonly;

GRANT USAGE ON SCHEMA public TO reckot_ai_public_readonly;
GRANT USAGE ON SCHEMA public TO reckot_ai_auth_readonly;
GRANT USAGE ON SCHEMA public TO reckot_ai_org_readonly;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM reckot_ai_public_readonly;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM reckot_ai_auth_readonly;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM reckot_ai_org_readonly;

GRANT SELECT (id, organization_id, category_id, title, slug, description, short_description, cover_image, start_at, end_at, timezone, event_type, location, venue_name, address_line_2, city, country, online_url, website, capacity, state, is_public, is_free, is_featured, created_at, updated_at) ON events_event TO reckot_ai_public_readonly;

GRANT SELECT (id, organization_id, category_id, title, slug, description, short_description, cover_image, start_at, end_at, timezone, event_type, location, venue_name, address_line_2, city, country, online_url, website, capacity, state, is_public, is_free, is_featured, created_at, updated_at, contact_email, contact_phone) ON events_event TO reckot_ai_auth_readonly;

GRANT SELECT (id, organization_id, category_id, title, slug, description, short_description, cover_image, start_at, end_at, timezone, event_type, location, venue_name, address_line_2, city, country, online_url, website, capacity, state, is_public, is_free, is_featured, created_at, updated_at, contact_email, contact_phone) ON events_event TO reckot_ai_org_readonly;

GRANT SELECT (id, name, slug, description, icon, color, is_active, display_order, created_at, updated_at) ON events_eventcategory TO reckot_ai_public_readonly;
GRANT SELECT (id, name, slug, description, icon, color, is_active, display_order, created_at, updated_at) ON events_eventcategory TO reckot_ai_auth_readonly;
GRANT SELECT (id, name, slug, description, icon, color, is_active, display_order, created_at, updated_at) ON events_eventcategory TO reckot_ai_org_readonly;

GRANT SELECT (id, event_id, name, price, quantity, description, max_per_order, sales_start, sales_end, is_active) ON tickets_tickettype TO reckot_ai_public_readonly;
GRANT SELECT (id, event_id, name, price, quantity, description, max_per_order, sales_start, sales_end, is_active) ON tickets_tickettype TO reckot_ai_auth_readonly;
GRANT SELECT (id, event_id, name, price, quantity, description, max_per_order, sales_start, sales_end, is_active) ON tickets_tickettype TO reckot_ai_org_readonly;

GRANT SELECT (id, name, slug, description, logo, website, created_at) ON orgs_organization TO reckot_ai_public_readonly;

GRANT SELECT (id, name, slug, description, logo, website, created_at) ON orgs_organization TO reckot_ai_auth_readonly;

GRANT SELECT (id, name, slug, description, logo, website, created_at, currency) ON orgs_organization TO reckot_ai_org_readonly;

GRANT SELECT (id, reference, event_id, user_id, status, delivery_method, total_amount, created_at, updated_at) ON tickets_booking TO reckot_ai_auth_readonly;
GRANT SELECT (id, reference, event_id, user_id, status, delivery_method, total_amount, created_at, updated_at) ON tickets_booking TO reckot_ai_org_readonly;

GRANT SELECT (id, booking_id, ticket_type_id, code, is_checked_in, checked_in_at) ON tickets_ticket TO reckot_ai_auth_readonly;
GRANT SELECT (id, booking_id, ticket_type_id, code, is_checked_in, checked_in_at) ON tickets_ticket TO reckot_ai_org_readonly;

GRANT SELECT (id, booking_id, reference, amount, service_fee, currency, provider, status, created_at, confirmed_at) ON payments_payment TO reckot_ai_org_readonly;

GRANT SELECT (id, event_id, total_revenue, platform_fees, net_revenue, tickets_sold, tickets_checked_in, orders_count, conversion_rate, page_views, unique_visitors, last_updated) ON analytics_eventmetrics TO reckot_ai_org_readonly;

GRANT SELECT (id, organization_id, total_revenue, total_fees_paid, net_revenue, total_tickets_sold, total_events, active_events, completed_events, total_attendees, average_ticket_price, last_updated) ON analytics_organizationmetrics TO reckot_ai_org_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reckot_ai_public_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reckot_ai_auth_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reckot_ai_org_readonly;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM reckot_ai_public_readonly;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM reckot_ai_auth_readonly;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM reckot_ai_org_readonly;
