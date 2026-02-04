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

## Documentation

- **[Database Schema](DATABASE_SCHEMA.md)** - Complete ER diagram and schema documentation
- **[AI Governance](AI_GOVERNANCE.md)** - Security framework for AI database queries

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
│   ├── ai/              # AI chat, support tickets, query execution
│   ├── analytics/       # Metrics and dashboards
│   ├── checkin/         # Event check-in and swag distribution
│   ├── core/            # User model, notifications, OTP
│   ├── events/          # Event management and customization
│   ├── marketing/       # Affiliate links and social sharing
│   ├── messaging/       # Email campaigns and templates
│   ├── orgs/            # Organizations and membership
│   ├── payments/        # Payment processing and refunds
│   ├── reports/         # Report generation and exports
│   ├── tickets/         # Ticket types, bookings, tickets
│   └── widgets/         # Embeddable event widgets
├── reckot/              # Project settings and config
├── templates/           # Django templates
├── static/              # Static assets (CSS, JS, images)
├── media/               # User-uploaded files
└── locale/              # Translations (English, French)
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

See [AI_GOVERNANCE.md](AI_GOVERNANCE.md) for full details.

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL 14+ (or SQLite for development)
- Redis 7+
- Node.js 18+ (for TailwindCSS)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Reckot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt  # or use uv
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Start Celery worker** (in another terminal)
   ```bash
   celery -A reckot worker -l info
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

See the complete [Database Schema Documentation](DATABASE_SCHEMA.md) with visual ER diagram.

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

Learn more in [AI_GOVERNANCE.md](AI_GOVERNANCE.md).

## Internationalization

Reckot supports multiple languages:
- English (default)
- French

To add translations:
```bash
python manage.py makemessages -l fr
# Edit locale/fr/LC_MESSAGES/django.po
python manage.py compilemessages
```

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.events

# With coverage
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
# Build and run
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
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
- Email: [your-email@example.com]

## Acknowledgments

- Django community for the excellent framework
- Unfold for the modern admin interface
- Google Gemini for AI capabilities
- All payment gateway providers for their APIs

---

**Built with care for event organizers worldwide**
