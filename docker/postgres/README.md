# PostgreSQL AI Read-Only Users Setup

This directory contains initialization scripts for creating AI read-only database users with RBAC (Role-Based Access Control).

## Overview

Three read-only PostgreSQL users are automatically created when the database container initializes:

1. **reckot_ai_public_readonly** - PUBLIC access level
2. **reckot_ai_auth_readonly** - AUTHENTICATED access level
3. **reckot_ai_org_readonly** - ORG_MEMBER access level

## Security Features

- Column-level permissions enforced at database level
- Read-only access (SELECT only)
- No INSERT, UPDATE, DELETE, or TRUNCATE permissions
- Password-protected with separate credentials
- Defense-in-depth with application-level validation

## Configuration

Set these environment variables in your `.env` file:

```bash
AI_PUBLIC_READONLY_PASSWORD=your_secure_password_1
AI_AUTH_READONLY_PASSWORD=your_secure_password_2
AI_ORG_READONLY_PASSWORD=your_secure_password_3
```

## Files

- `init-readonly-users.sql` - SQL script with column-level grants
- `init-readonly-users.sh` - Shell wrapper for password injection
- `README.md` - This file

## Verification

```bash
docker-compose exec db psql -U reckot_ai_public_readonly -d reckot -c "SELECT COUNT(*) FROM events_event;"
```
