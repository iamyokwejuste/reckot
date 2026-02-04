# Docker Configuration

This directory contains all Docker-related configuration files for the Reckot project.

## Structure

```
docker/
├── Dockerfile
├── entrypoint.sh
└── postgres/
    ├── init-readonly-users.sql
    ├── init-readonly-users.sh
    └── README.md
```

## Files

### Dockerfile
Multi-stage production Dockerfile with:
- Python 3.12.8 slim base
- UV package manager for fast installs
- Non-root user (appuser)
- Build-time static file collection
- Health checks configured

### entrypoint.sh
Container entrypoint that:
- Waits for database availability
- Runs migrations (if RUN_MIGRATIONS=true)
- Collects static files (if COLLECT_STATIC=true)
- Starts the application server

### postgres/
PostgreSQL initialization scripts for creating read-only AI database users with RBAC.
See [postgres/README.md](postgres/README.md) for details.

## Usage

Build the image:
```bash
docker-compose build
```

Start services:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f web
```

## Environment Variables

See `.env.example` in project root for all available variables.

Key variables:
- `RUN_MIGRATIONS` - Run migrations on startup (default: false)
- `COLLECT_STATIC` - Collect static files on startup (default: false)
- `PORT` - Application port (default: 8000)
- `AI_*_READONLY_PASSWORD` - Passwords for AI read-only database users
