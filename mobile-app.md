# Reckot Mobile App Specification

## Platform Overview
Event management and ticketing platform for African markets with AI capabilities, mobile money payments, and offline check-in.

## Design System
**Colors:** Light mode (bg: #fafafa, primary: #09090b), Dark mode (bg: #09090b, primary: #fafafa)
**Typography:** Inter font, weights 400-700
**Components:** Rounded corners (0.5-1rem), shadows, 48px input height, full rounded buttons
**Icons:** Lucide icon library

## Core Features

### User Features
- Authentication (email/password, phone/OTP)
- Event discovery with filters and search
- Ticket purchase with mobile money (Campay, Flutterwave)
- QR code tickets with offline display
- Payment tracking and refund requests

### Organizer Features
- Organization and team management
- Event creation with ticket types
- Real-time analytics dashboard
- QR code check-in (works offline)
- Financial management (withdrawals, refunds)
- Marketing tools (affiliate links, campaigns)

### AI Features (Google Gemini)
- Conversational assistant for queries
- Content generation (descriptions, social posts)
- Sales prediction and pricing optimization
- Support ticket analysis

## Payment Methods
- Mobile Money: Campay (MTN/Orange Cameroon), Flutterwave (Ghana/Uganda)
- Cards: Visa, Mastercard via Flutterwave
- Offline: Cash or bank transfer

## Currencies
XAF, XOF, USD, EUR, GBP, NGN, GHS, UGX

## Key Flows
1. User browses events, selects tickets, pays via mobile money, receives QR ticket
2. Organizer creates event, sets up tickets, publishes, monitors sales, checks in attendees
3. Offline check-in: Download attendee list, scan QR codes offline, sync when online

## Technical
- API: Django REST Framework
- Real-time: WebSockets for chat
- Auth: JWT tokens
- Platform: iOS 14+, Android 8.0+
- Suggested: React Native or Flutter

## Required Pages/Screens

### Public Pages (Unauthenticated)
- Landing/Home page
- Event discovery/browse
- Event detail page
- Login page
- Sign up page
- Password reset
- Ticket lookup (for guests)
- Privacy policy
- Terms of service

### User Pages (Authenticated)
- My tickets list
- Ticket detail with QR code
- User profile
- Account settings
- Checkout flow (attendee info, payment method, order summary)
- Payment success/failure
- Payment tracking
- Invoice download
- Refund request

### Organizer Pages
- Organizations list
- Create organization
- Organization dashboard
- Events list
- Create event (multi-step)
- Event dashboard (stats, bookings)
- Edit event
- Manage ticket types
- Checkout questions setup
- Coupons management
- Event customization (branding)
- Analytics dashboard (charts, graphs)
- Attendee list
- Export reports
- Check-in dashboard
- QR scanner for check-in
- Manual check-in
- Financial dashboard
- Withdrawal requests
- Withdrawal history
- Refund management
- Refund processing
- Team management
- Invite members
- Affiliate links
- Message campaigns
- Campaign analytics

### AI Features Pages
- AI assistant chat
- AI content generator
- AI sales prediction
- AI pricing optimization
- AI marketing strategy
- Support tickets list
- Create support ticket
- Ticket detail/conversation

### Settings & Notifications
- Notification center
- Notification preferences
- Theme selection (light/dark)
- Language selection
- AI features toggle
- Security settings

### Navigation
- Bottom tab bar (Home, Tickets, Create/Manage, AI, Profile)
- Side drawer (for organizer features)
- Search interface
