# Reckot - Event Management & Ticketing Platform

**Reckot** is a modern, AI-powered event management and ticketing platform built with Django. It provides comprehensive tools for event organizers to create, manage, and monetize events while offering attendees a seamless ticket purchasing experience.

## Key Features

### Event Management
- **Multi-tenant architecture** with organization-based access control
- **Event categories** and customizable event pages
- **Flexible ticket types** with pricing and availability controls
- **Event customization** with themes, colors, and custom CSS
- **Flyer generation** system for social media promotion

### Ticketing & Sales
- **Guest checkout** for purchases without account creation
- **Multiple payment gateways** (CamPay, PawaPay, Flutterwave)
- **Coupon system** with percentage and fixed discounts
- **Booking management** with confirmed, pending, and refunded states
- **QR code tickets** with unique codes for check-in

### Payments & Withdrawals
- **Multi-currency support** (XAF, XOF, USD, EUR, NGN, GHS, UGX)
- **Platform fee management** per organization subscription tier
- **Refund processing** with admin approval workflow
- **Withdrawal requests** for organizations to receive their revenue
- **Invoice generation** for all transactions

### Check-in & Swag
- **QR code scanning** for ticket validation
- **Swag item tracking** and distribution
- **Real-time check-in analytics**

### Marketing
- **Affiliate link system** with commission tracking
- **Social sharing** analytics
- **Event featured listings** with approval workflow

### AI & Support
- **AI-powered chat** using Google Gemini
- **Natural language database queries**
- **Support ticket system** with AI-suggested solutions
- **Predictive analytics** for event performance

### Analytics & Reports
- **Real-time dashboards** for events, payments, and organizations
- **Revenue tracking** with platform fees breakdown
- **Conversion rate analytics**
- **Daily metrics** aggregation

## Architecture

### Technology Stack
- **Backend:** Django 5.x + Python 3.12
- **Database:** PostgreSQL/SQLite (configurable)
- **Cache:** Redis with django-redis
- **Task Queue:** Celery with Redis broker
- **AI:** Google Gemini API
- **Frontend:** Django templates + TailwindCSS + HTMX
- **Admin:** Unfold (modern Django admin theme)
- **Authentication:** django-allauth with Google OAuth

### Project Structure

```
reckot/
├── apps/
│   ├── ai/
│   ├── analytics/
│   ├── checkin/
│   ├── core/
│   ├── events/
│   ├── marketing/
│   ├── messaging/
│   ├── orgs/
│   ├── payments/
│   ├── reports/
│   ├── tickets/
│   └── widgets/
├── reckot/
├── templates/
├── static/
├── media/
└── locale/
```

## Security Features

### Current Implementation
- CSRF protection
- XSS filtering
- Secure cookies (HTTPS only in production)
- Rate limiting middleware
- Email and phone verification
- Role-based access control (RBAC)

### AI Governance (In Development)
Our new **AI Governance Framework** provides enterprise-grade security for AI-powered database queries:

- **Read-only database users** with column-level permissions
- **Data classification** (Public, Authenticated, Organization, Sensitive)
- **Query validation** to prevent SQL injection and data leakage
- **Audit trail** for all AI-generated queries
- **Rate limiting** per user and access level
- **Risk scoring** for query analysis


## Getting Started

### Prerequisites
- **Docker** and **Docker Compose** (recommended)
- OR Python 3.12+, PostgreSQL 14+, Redis 7+

### Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Reckot
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Start all services**
   ```bash
   docker-compose -f docker-compose-dev.yml up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose -f docker-compose-dev.yml exec web python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   docker-compose -f docker-compose-dev.yml exec web python manage.py createsuperuser
   ```

6. **Access the application**
   - Web: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Health: http://localhost:8000/health/

### Manual Installation (Without Docker)

1. **Clone and setup virtual environment**
   ```bash
   git clone <repository-url>
   cd Reckot
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```

4. **Run migrations and create superuser**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Start services**
   ```bash
   redis-server &
   python manage.py runserver &
   celery -A reckot worker -l info &
   ```

## Docker Commands Reference

### Starting Services
```bash
docker-compose -f docker-compose-dev.yml up -d
docker-compose -f docker-compose-dev.yml ps
```

### Viewing Logs
```bash
docker-compose -f docker-compose-dev.yml logs -f
docker-compose -f docker-compose-dev.yml logs -f web
docker-compose -f docker-compose-dev.yml logs -f celery_worker
```

### Running Django Commands
```bash
docker-compose -f docker-compose-dev.yml exec web python manage.py migrate
docker-compose -f docker-compose-dev.yml exec web python manage.py createsuperuser
docker-compose -f docker-compose-dev.yml exec web python manage.py shell
docker-compose -f docker-compose-dev.yml exec web python manage.py makemigrations
docker-compose -f docker-compose-dev.yml exec web python manage.py collectstatic --noinput
```

### Stopping Services
```bash
docker-compose -f docker-compose-dev.yml stop
docker-compose -f docker-compose-dev.yml down
docker-compose -f docker-compose-dev.yml down -v
```

### Rebuilding After Code Changes
```bash
docker-compose -f docker-compose-dev.yml up -d --build
docker-compose -f docker-compose-dev.yml restart web
```

### Database Operations
```bash
docker-compose -f docker-compose-dev.yml exec db psql -U reckot -d reckot
docker-compose -f docker-compose-dev.yml exec web python manage.py dbshell
```

### Redis Operations
```bash
docker-compose -f docker-compose-dev.yml exec redis redis-cli
docker-compose -f docker-compose-dev.yml exec redis redis-cli FLUSHALL
```

## Local Development

### Running Locally with Port Access

#### Option 1: Basic Local Access (localhost only)
```bash
redis-server

python manage.py runserver

celery -A reckot worker -l info

celery -A reckot beat -l info
```

#### Option 2: Expose on All Network Interfaces (accessible from other devices)
```bash
python manage.py runserver 0.0.0.0:8000

ALLOWED_HOSTS=*
```

#### Option 3: WSL2 Port Forwarding (Windows Subsystem for Linux)
If you're running in WSL2, Windows should automatically forward ports. If not:

```powershell
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=<WSL-IP>

wsl hostname -I
```

To remove port forwarding later:
```powershell
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
```

#### Option 4: Using ngrok for External Access (testing webhooks, etc.)
```bash
ngrok http 8000
```

### Development Services Setup

#### PostgreSQL Setup
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib

sudo -u postgres psql
postgres=# CREATE DATABASE reckot;
postgres=# CREATE USER reckot WITH PASSWORD 'changeme';
postgres=# GRANT ALL PRIVILEGES ON DATABASE reckot TO reckot;
postgres=# \q

DB_ENGINE=django.db.backends.postgresql
DB_NAME=reckot
DB_USER=reckot
DB_PASSWORD=changeme
DB_HOST=localhost
DB_PORT=5432
```

#### SQLite Setup (Simpler for Development)
```bash
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

#### Redis Setup
```bash
sudo apt update
sudo apt install redis-server

sudo systemctl start redis-server

redis-cli ping

REDIS_URL=redis://127.0.0.1:6379/1
```

### Running All Services Together

Use this script to start all services (create `start-dev.sh`):

```bash
redis-server --daemonize yes

python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

celery -A reckot worker -l info &
CELERY_PID=$!

celery -A reckot beat -l info &
BEAT_PID=$!

echo "Services started:"
echo "Django: PID $DJANGO_PID (http://localhost:8000)"
echo "Celery: PID $CELERY_PID"
echo "Beat: PID $BEAT_PID"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $DJANGO_PID $CELERY_PID $BEAT_PID; exit" INT
wait
```

Make it executable and run:
```bash
chmod +x start-dev.sh
./start-dev.sh
```

### Accessing the Application

Once running, access:
- **Main site**: http://localhost:8000
- **Admin panel**: http://localhost:8000/admin
- **API endpoints**: http://localhost:8000/api/
- **Health check**: http://localhost:8000/health/

### Common Development Tasks

```bash
python manage.py makemigrations

python manage.py migrate

python manage.py collectstatic --noinput

python manage.py shell
>>> from apps.core.models import User
>>> from apps.orgs.models import Organization

python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()

tail -f logs/django.log
```

### Troubleshooting

#### Port Already in Use
```bash
lsof -i :8000
netstat -ano | findstr :8000

kill -9 <PID>
taskkill /PID <PID> /F

python manage.py runserver 0.0.0.0:8080
```

#### Redis Connection Issues
```bash
redis-cli ping

redis-server

tail -f /var/log/redis/redis-server.log
```

#### Database Connection Issues
```bash
psql -U reckot -d reckot -h localhost

sudo systemctl status postgresql

sudo systemctl restart postgresql
```

#### Migration Issues
```bash
python manage.py migrate --fake app_name zero
python manage.py migrate app_name

dropdb reckot && createdb reckot
python manage.py migrate
```

### Environment Variables

Key environment variables (see `.env.example` for full list):

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=reckot
DB_USER=reckot
DB_PASSWORD=changeme
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# AI
GEMINI_API_KEY=your-gemini-api-key

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Payments
CAMPAY_APP_USERNAME=
CAMPAY_APP_PASSWORD=
CAMPAY_PERMANENT_TOKEN=
```

## Database Schema

The platform uses a comprehensive relational schema with 35+ tables. Key entity relationships:

- **Users** belong to multiple **Organizations** through **Memberships**
- **Organizations** host **Events** with **TicketTypes**
- Users/Guests create **Bookings** with **Tickets**
- **Payments** process **Bookings** via **PaymentGatewayConfigs**
- **Events** track analytics through **EventMetrics**
- **AI** conversations help users through **AIConversation** and **AIMessage**

## AI Features

### Current Capabilities
1. **Natural Language Queries** - Ask questions like "How many tickets were sold this month?"
2. **Event Description Generation** - AI-generated event descriptions
3. **Support Ticket Analysis** - Automatic issue categorization and suggested solutions
4. **Social Media Post Generation** - AI-crafted social posts for events
5. **Predictive Analytics** - Sales predictions and pricing optimization

### Upcoming: AI Governance
We're implementing a secure AI query system that:
- Uses read-only database users (not Django ORM)
- Enforces column-level permissions
- Prevents access to sensitive data (emails, phones, credentials)
- Provides full audit trails
- Implements rate limiting

## Internationalization

Reckot supports multiple languages:
- English (default)
- French

To add translations:
```bash
python manage.py makemessages -l fr
python manage.py compilemessages
```

## Testing

```bash
python manage.py test

python manage.py test apps.events

coverage run --source='.' manage.py test
coverage report
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use strong `SECRET_KEY`
- [ ] Set up HTTPS
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Redis for caching
- [ ] Configure Celery workers
- [ ] Set up static file serving (WhiteNoise or CDN)
- [ ] Configure email backend (SMTP or SendGrid)
- [ ] Enable CSRF_COOKIE_SECURE and SESSION_COOKIE_SECURE
- [ ] Set up logging and monitoring
- [ ] Configure backup strategy

### Docker Deployment
```bash
docker-compose up -d

docker-compose exec web python manage.py migrate

docker-compose exec web python manage.py createsuperuser
```

## License

[Add your license here]

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For questions or issues:
- Create an issue on GitHub
- Email: [yokwejuste@gmail.com]

## Acknowledgments

- Django community for the excellent framework
- Unfold for the modern admin interface
- Google Gemini for AI capabilities
- All payment gateway providers for their APIs

---

**Built with care for event organizers worldwide**
