# Reckot Mobile App Specification

## Platform Overview
Reckot is a comprehensive event management and ticketing platform designed specifically for African markets. The mobile app provides seamless event discovery, ticket purchasing with local payment methods (mobile money), and powerful organizer tools including offline QR code check-in. Built with AI capabilities powered by Google Gemini for content generation, sales prediction, and intelligent assistance.

## Design System

### Colors
- **Light Mode:** Background #fafafa, Primary #09090b, Accent colors for status indicators
- **Dark Mode:** Background #09090b, Primary #fafafa, maintains accessibility contrast
- **Semantic Colors:** Success (green), Warning (yellow/orange), Error (red), Info (blue)

### Typography
- **Font Family:** Inter (system fallback: San Francisco on iOS, Roboto on Android)
- **Weights:** Regular (400), Medium (500), Semibold (600), Bold (700)
- **Sizes:** Heading (24-32px), Subheading (18-20px), Body (14-16px), Caption (12px)

### Components
- **Buttons:** Full rounded corners, 48px height for primary actions, 40px for secondary
- **Cards:** Rounded corners (0.5-1rem), subtle shadows, elevation for hierarchy
- **Inputs:** 48px height, rounded corners, clear focus states
- **Icons:** Lucide icon library for consistent visual language

---

## Core Features & Functionalities

### 1. User Features (Attendee Experience)

#### 1.1 Authentication & Account Management
**What it does:** Secure user registration and login using email/password or phone number with OTP verification. Supports password recovery and account security settings.

**Key Functionalities:**
- Email/password registration with verification email
- Phone number registration with SMS OTP (6-digit code)
- Social login (Google, Facebook - optional)
- Password reset via email link
- Biometric login (Face ID, Touch ID, fingerprint) after initial setup
- Multi-device session management
- Account deletion with data export option

#### 1.2 Event Discovery & Search
**What it does:** Browse and discover events with advanced filtering, search, and location-based recommendations. Users can explore trending events, nearby events, and events by category.

**Key Functionalities:**
- Browse all published events with infinite scroll
- Search by event name, organizer, location, or keywords
- Filter by:
  - Date range (today, this weekend, this month, custom)
  - Location (city, country, radius from current location)
  - Category (music, sports, conference, networking, etc.)
  - Price range (free, under 5000 XAF, etc.)
  - Event type (online, in-person, hybrid)
- Sort by: date, popularity, price, distance
- Map view showing events near user's location
- Save events to favorites/watchlist
- Share events via social media, messaging apps, or link
- Event recommendations based on user preferences and past purchases

#### 1.3 Ticket Purchase Flow
**What it does:** Complete end-to-end ticket purchasing with mobile money, card payments, or offline payment options. Handles attendee information collection, payment processing, and ticket delivery.

**Key Functionalities:**
- Select ticket types and quantities
- Apply promo codes/coupons with real-time discount calculation
- Fill out custom checkout questions (name, phone, dietary preferences, etc.)
- Choose payment method (mobile money, card, pay at event)
- Mobile money payment:
  - Campay: MTN Mobile Money, Orange Money (Cameroon)
  - Flutterwave: Mobile money for Ghana, Uganda, Nigeria
  - Receive USSD push notification for payment authorization
  - Enter mobile money PIN on phone to confirm
- Card payment via Flutterwave (Visa, Mastercard)
- Payment status tracking in real-time
- Automatic retry on payment failure
- Receive ticket via email and in-app immediately after payment
- Download tickets as PDF
- Add tickets to Apple Wallet / Google Pay (future)

#### 1.4 QR Code Tickets & Offline Access
**What it does:** Generates secure QR code tickets that work offline. Users can access tickets without internet connection for reliable event entry.

**Key Functionalities:**
- Unique QR code per ticket (encrypted booking reference)
- Offline ticket display (cached locally)
- Ticket details: event name, date, location, seat/tier, attendee name
- Transfer tickets to friends (transfer ownership)
- Multiple tickets per booking grouped together
- Ticket status indicator (valid, used, refunded, expired)
- Brightness boost for scanning in low light
- Backup barcode format for compatibility

#### 1.5 Payment Tracking & Refunds
**What it does:** Track payment status, view transaction history, request refunds, and download invoices for purchases.

**Key Functionalities:**
- View all payments and their status (pending, completed, failed, refunded)
- Payment details: amount, currency, method, date, transaction ID
- Request refund with reason selection
- Track refund status (submitted, approved, denied, processed)
- Receive refund notifications
- Download invoices as PDF
- Payment receipts via email
- Refund timeline: 3-5 business days to original payment method

---

### 2. Organizer Features (Event Management)

#### 2.1 Organization & Team Management
**What it does:** Create and manage organizations, invite team members with role-based permissions, and control access to events and financial data.

**Key Functionalities:**
- Create organization with name, logo, website, description
- Organization slug for custom URLs
- Default currency selection (XAF, USD, GHS, UGX, etc.)
- Team member roles:
  - Owner: Full access, cannot be removed
  - Admin: All permissions except delete organization
  - Manager: Create/edit events, manage tickets, view reports
  - Member: Create/edit events, check-in attendees
  - Viewer: View reports only
- Invite members via email with role assignment
- Pending invitation management (resend, cancel)
- Remove team members
- Custom role creation with granular permissions (enterprise feature)
- Audit log of team actions

#### 2.2 Event Creation & Management
**What it does:** Multi-step event creation wizard to publish professional events with tickets, branding, and custom settings.

**Key Functionalities:**
- **Step 1: Basic Info**
  - Event name, slug (for custom URL)
  - Category selection
  - Description (rich text with AI assistance)
  - Cover image upload (max 5MB, auto-resize)
  - Event type (in-person, online, hybrid)

- **Step 2: Date & Location**
  - Start date/time with timezone
  - End date/time
  - Venue name and address (with map picker)
  - Online event link (for virtual events)

- **Step 3: Ticket Types**
  - Add multiple ticket tiers (VIP, Regular, Early Bird, etc.)
  - Set price and currency per ticket type
  - Total quantity available
  - Sales start/end dates (optional)
  - Minimum/maximum tickets per order
  - Ticket description

- **Step 4: Customization**
  - Custom checkout questions (text, dropdown, checkbox)
  - Event branding (colors, logo)
  - Email templates customization
  - Social media preview optimization

- **Step 5: Review & Publish**
  - Preview event page
  - Publish immediately or schedule
  - Draft mode for later completion
  - Generate shareable event link

- **Event States:**
  - DRAFT: Not visible to public
  - PUBLISHED: Live and accepting bookings
  - CLOSED: No longer accepting bookings
  - ARCHIVED: Past event, hidden from discovery

#### 2.3 Ticket Type Management
**What it does:** Configure and manage different ticket tiers, pricing, availability, and sales windows for each event.

**Key Functionalities:**
- Create unlimited ticket types per event
- Set individual prices and currencies
- Control availability (quantity, sold out status)
- Sales schedule (start/end dates for early bird, presale)
- Activate/deactivate ticket types without deleting
- Reorder ticket types for display priority
- Duplicate ticket types for quick setup
- Track sales per ticket type in real-time

#### 2.4 Real-Time Analytics Dashboard
**What it does:** Comprehensive analytics showing ticket sales, revenue, attendee demographics, and sales trends with interactive charts.

**Key Functionalities:**
- **Key Metrics:**
  - Total tickets sold
  - Total revenue (gross and net after fees)
  - Average ticket price
  - Conversion rate (page views to purchases)
  - Revenue per ticket type

- **Charts & Graphs:**
  - Sales over time (line chart)
  - Ticket type distribution (pie chart)
  - Payment method breakdown
  - Daily/weekly/monthly revenue trends
  - Geographic distribution of attendees (map)

- **Real-time Updates:**
  - Live sales counter
  - Recent bookings feed
  - Payment status updates
  - WebSocket connection for instant updates

#### 2.5 QR Code Check-In System (Offline Support)
**What it does:** Scan attendee QR codes for event entry with full offline functionality. Download attendee list before event, scan tickets without internet, sync data when online.

**Key Functionalities:**
- **Pre-Event Setup:**
  - Download complete attendee list to device
  - Encrypted local storage of attendee data
  - Check-in status sync indicator

- **QR Scanner:**
  - Camera-based QR code scanning
  - Instant validation (offline mode)
  - Duplicate check-in prevention
  - Visual/audio feedback on successful scan
  - Invalid ticket warnings
  - Already checked-in notifications

- **Manual Check-In:**
  - Search attendee by name, email, or booking reference
  - Manual check-in button for QR code issues
  - Attendee verification details display

- **Check-In Dashboard:**
  - Total attendees: expected vs. checked in
  - Real-time check-in counter
  - Check-in activity log with timestamps
  - Filter by ticket type, check-in status
  - Export check-in report

- **Offline Mode:**
  - Full functionality without internet
  - Local data validation
  - Automatic background sync when connected
  - Conflict resolution for multi-device check-ins
  - Sync status indicator

#### 2.6 Financial Management
**What it does:** Track earnings, request withdrawals, manage refunds, and view financial reports for payouts and transactions.

**Key Functionalities:**
- **Financial Dashboard:**
  - Total earnings (all time, per event)
  - Available balance (after 24hr hold post-event)
  - Pending withdrawals
  - Platform fees breakdown
  - Net revenue calculations

- **Withdrawal Requests:**
  - Minimum: No minimum withdrawal amount
  - Request withdrawal to mobile money account
  - Processing time: 24 hours after event ends
  - Payout timeline: 24 hours after approval
  - Withdrawal history with transaction IDs
  - Failed withdrawal retry

- **Refund Management:**
  - View refund requests from attendees
  - Approve or deny with reason
  - Partial refund option
  - Automatic refund processing on approval
  - Refund impact on revenue reports
  - Refund policy customization per event

#### 2.7 Marketing Tools
**What it does:** Create affiliate programs, send message campaigns, and track marketing performance to boost ticket sales.

**Key Functionalities:**
- **Affiliate Links:**
  - Generate unique affiliate links
  - Commission rate setting (percentage or fixed)
  - Track clicks, conversions, and commission earned
  - Affiliate leaderboard
  - Automatic commission payouts

- **Message Campaigns:**
  - Send targeted emails/SMS to attendees
  - Segmentation: all attendees, ticket type, checked-in status
  - Campaign templates (event reminders, updates, promotions)
  - Schedule campaigns for future delivery
  - Track open rates, click rates
  - A/B testing support (enterprise)

- **Promo Codes/Coupons:**
  - Create discount codes (percentage or fixed amount)
  - Usage limits (total uses, per-user limit)
  - Expiration dates
  - Apply to specific ticket types
  - Track coupon usage and revenue impact

---

### 3. AI Features (Powered by Google Gemini)

#### 3.1 AI Assistant Chat
**What it does:** Conversational AI assistant to help users find events, answer questions, and assist organizers with event management tasks.

**Key Functionalities:**
- Natural language queries (e.g., "Find music events this weekend")
- Event recommendations based on conversation
- Answer FAQs about platform, payments, refunds
- Help organizers with event setup guidance
- Multi-turn conversations with context retention
- Voice input support
- Suggested follow-up questions

#### 3.2 AI Content Generator
**What it does:** Generate compelling event descriptions, social media posts, email content, and marketing copy using AI.

**Key Functionalities:**
- Event description generation from title and category
- Social media post variations (Twitter, Facebook, Instagram)
- Email campaign content (invitations, reminders, thank you)
- Generate catchy event taglines
- Tone adjustment (professional, casual, exciting)
- Multiple variations to choose from
- Edit and refine generated content
- Multilingual content generation

#### 3.3 AI Sales Prediction
**What it does:** Predict ticket sales trends, forecast revenue, and provide insights to help organizers optimize their events.

**Key Functionalities:**
- Forecast total tickets to be sold
- Revenue prediction with confidence intervals
- Peak sales periods identification
- Comparison with similar past events
- Optimal pricing suggestions
- Sales velocity tracking
- Risk alerts (low sales, overselling)

#### 3.4 AI Pricing Optimization
**What it does:** Analyze market data and event characteristics to suggest optimal ticket pricing for maximum revenue and attendance.

**Key Functionalities:**
- Recommended price range per ticket type
- Dynamic pricing suggestions based on demand
- Competitor pricing analysis
- Price elasticity insights
- Early bird vs. regular pricing strategy
- Revenue maximization vs. attendance maximization options

#### 3.5 AI Marketing Strategy
**What it does:** Generate personalized marketing strategies, identify target audiences, and suggest promotional tactics.

**Key Functionalities:**
- Target audience identification
- Marketing channel recommendations (social, email, affiliates)
- Campaign timing suggestions
- Content themes and messaging ideas
- Budget allocation recommendations
- Influencer partnership opportunities

#### 3.6 Support Ticket Analysis
**What it does:** AI-powered support system that analyzes user queries, suggests solutions, and routes tickets to appropriate team members.

**Key Functionalities:**
- Automatic ticket categorization
- Sentiment analysis (urgent, frustrated, satisfied)
- Suggested responses for common issues
- Knowledge base article recommendations
- Priority assignment
- Auto-response for frequently asked questions

---

## Payment Methods & Processing

### Mobile Money
**Campay Integration (Cameroon):**
- MTN Mobile Money (MTN MoMo)
- Orange Money
- USSD push notification sent to user's phone
- User authorizes payment with PIN
- Instant confirmation
- Agent name for withdrawal: TAKWID GROUP

**Flutterwave Integration (Multi-Country):**
- Ghana: MTN, Vodafone, AirtelTigo
- Uganda: MTN, Airtel
- Nigeria: All major networks
- Card payments: Visa, Mastercard
- 3D Secure authentication for cards

### Location-Based Payment Filtering
- IP geolocation using ipinfo.io
- Cameroon (CM): Show only Campay and Offline options
- Other countries: Show all available methods (Flutterwave, Offline)
- Fallback to all methods if geolocation fails

### Offline Payment
- "Pay at Event" option
- Booking reserved, payment pending
- Organizer marks as paid manually or attendee pays at entrance
- No transaction fees for offline payments

### Transaction Fees
- Mobile money withdrawal fee included in total
- Platform service fee (2-7% based on organization plan)
- Transparent fee breakdown before payment

---

## Currency Support
- **XAF** - Central African CFA Franc (Cameroon, Chad, etc.)
- **XOF** - West African CFA Franc (Senegal, Ivory Coast, etc.)
- **USD** - US Dollar
- **EUR** - Euro
- **GBP** - British Pound
- **NGN** - Nigerian Naira
- **GHS** - Ghanaian Cedi
- **UGX** - Ugandan Shilling

Currency is set at organization level and applies to all events created by that organization.

---

## User Flows

### Flow 1: Attendee Ticket Purchase
1. User opens app and browses events on home screen
2. Searches for "music festival" or filters by category
3. Taps on event card to view details
4. Reads description, sees ticket types and prices
5. Selects ticket type (e.g., VIP - 2 tickets)
6. Taps "Get Tickets" button
7. Fills out attendee details form (name, email, phone)
8. Answers custom checkout questions if any
9. Reviews order summary with price breakdown
10. Selects payment method (Mobile Money - Campay)
11. Enters phone number (237 6XX XXX XXX)
12. Confirms payment
13. Receives USSD push on phone, enters PIN
14. Payment confirmed, ticket generated
15. Views ticket with QR code in "My Tickets"
16. Receives ticket via email
17. Downloads PDF ticket for backup

### Flow 2: Organizer Event Creation & Management
1. Organizer logs in and navigates to "Create Event"
2. Enters event name, category, and description
3. Uses AI to generate compelling description
4. Uploads event cover image
5. Sets event date, time, and venue location
6. Adds ticket types:
   - Early Bird - 5000 XAF (50 tickets, sales end 2 weeks before)
   - Regular - 7500 XAF (200 tickets)
   - VIP - 15000 XAF (30 tickets)
7. Adds custom checkout questions (dietary preferences)
8. Customizes event branding colors
9. Reviews and publishes event
10. Shares event link on social media
11. Monitors sales on analytics dashboard
12. Creates promo code "LAUNCH20" for 20% off
13. Sends email campaign to past attendees
14. Tracks sales in real-time
15. Downloads attendee list 1 day before event
16. On event day, uses QR scanner to check in attendees
17. Requests withdrawal 24 hours after event
18. Receives payout to mobile money account

### Flow 3: Offline QR Check-In
1. Organizer opens Reckot app on event day morning
2. Navigates to event check-in dashboard
3. Taps "Download Attendee List" (250 attendees)
4. App downloads encrypted attendee data
5. Shows "Offline Mode Ready" indicator
6. At event entrance (no internet signal)
7. Organizer opens QR scanner
8. Attendee shows QR code on phone
9. Organizer scans QR code
10. App validates ticket offline (checks local database)
11. Shows green success screen with attendee name
12. Attendee name marked as checked-in locally
13. Attendee enters event
14. Process repeats for 250 attendees throughout day
15. Organizer returns to area with WiFi
16. App automatically syncs all 250 check-ins to server
17. Dashboard updates with final check-in count

### Flow 4: Attendee Refund Request
1. User realizes they can't attend event
2. Opens "My Tickets" and selects ticket
3. Taps "Request Refund" button
4. Selects reason: "Can no longer attend"
5. Adds optional comment
6. Submits refund request
7. Organizer receives notification
8. Organizer reviews request in refund management
9. Organizer approves refund
10. System processes refund automatically
11. User receives refund notification
12. Refund processed to original payment method in 3-5 days
13. Ticket marked as "Refunded" and QR code invalidated

---

## Required Pages/Screens (Detailed)

### Public Pages (Unauthenticated)

#### Landing/Home Page
- Hero section with app value proposition
- Featured/trending events carousel
- Event categories grid
- Search bar
- "Sign Up" and "Login" CTAs
- Platform statistics (total events, organizers, tickets sold)
- Footer with links

#### Event Discovery/Browse
- Search bar with autocomplete
- Filter sidebar/bottom sheet (category, date, location, price)
- Event cards with image, title, date, location, price from
- Infinite scroll pagination
- Sort dropdown (date, popularity, price)
- Map view toggle
- Favorites icon on each card

#### Event Detail Page
- Event cover image (full width)
- Event title, date, time, location
- Organizer name and logo
- Event description (rich text)
- Ticket types with prices and availability
- "Sales start" or "Sold out" badges
- "Get Tickets" button (disabled if event ended/closed)
- Share button
- Add to favorites
- Similar events section
- For ended/closed events: "Event has ended" or "Event is closed" message

#### Login Page
- Email and password fields
- "Forgot Password?" link
- "Login" button
- Social login buttons (Google, Facebook)
- "Don't have an account? Sign up" link
- Biometric login option (if previously set up)

#### Sign Up Page
- Choice: Email or Phone registration
- Email flow: email, password, confirm password
- Phone flow: phone number, send OTP, verify OTP
- Terms of service and privacy policy checkboxes
- "Create Account" button
- "Already have an account? Login" link

#### Password Reset
- Enter email address
- "Send Reset Link" button
- Check email message
- Link opens app to reset password page
- Enter new password, confirm password
- "Reset Password" button

#### Ticket Lookup (for Guests)
- For users without account
- Enter booking reference or email
- View ticket details and QR code
- Download ticket PDF
- Request refund option

#### Privacy Policy
- Scrollable document
- Data collection and usage
- User rights
- Contact information

#### Terms of Service
- Scrollable document
- User agreements
- Prohibited activities
- Refund policies
- Dispute resolution

---

### User Pages (Authenticated Attendees)

#### My Tickets List
- Tabs: Upcoming, Past, Refunded
- Ticket cards showing event image, name, date
- "View Ticket" button
- Empty state: "No tickets yet. Browse events to get started"
- Pull to refresh

#### Ticket Detail with QR Code
- Large QR code (centered, scannable)
- Ticket information:
  - Event name and date
  - Attendee name
  - Ticket type
  - Booking reference
  - Purchase date
- "Transfer Ticket" button
- "Request Refund" button (if allowed)
- "Download PDF" button
- "Add to Wallet" button (future)
- Brightness boost toggle for scanning

#### User Profile
- Profile photo upload
- Name, email, phone number
- Edit profile information
- Past events attended (count)
- Favorite event categories
- Account creation date

#### Account Settings
- Change password
- Email preferences (marketing emails toggle)
- Push notification settings
- Biometric login toggle
- Language selection
- Theme (light/dark/system)
- Delete account (with confirmation)

#### Checkout Flow

**Step 1: Attendee Information**
- Number of tickets selected
- Form for each attendee:
  - Full name
  - Email address
  - Phone number
  - Custom questions (if any)
- "Continue to Payment" button

**Step 2: Payment Method Selection**
- Available payment methods (based on location):
  - Mobile Money (Campay or Flutterwave)
  - Credit/Debit Card
  - Pay at Event
- Phone number input for mobile money
- Carrier detection (MTN/Orange)
- Promo code field
- Order summary sidebar:
  - Ticket items
  - Subtotal
  - Transaction fee
  - Discount (if coupon applied)
  - Total

**Step 3: Order Review**
- Review all details
- Terms and conditions checkbox
- "Confirm and Pay" button

#### Payment Success/Failure

**Success Screen:**
- Green checkmark icon
- "Payment Successful!" message
- Order details
- "View Ticket" button
- "Download PDF" button
- Confetti animation

**Failure Screen:**
- Red X icon
- "Payment Failed" message
- Error reason (insufficient funds, timeout, etc.)
- "Retry Payment" button
- "Contact Support" link

#### Payment Tracking
- List of all payments
- Status badges (Pending, Completed, Failed, Refunded)
- Payment details: date, amount, method, transaction ID
- Tap to expand for more details
- Filter by status

#### Invoice Download
- Generate PDF invoice
- Invoice includes:
  - Reckot logo and details
  - Customer information
  - Event details
  - Itemized charges
  - Payment method
  - Transaction ID
- "Download" and "Share" options

#### Refund Request
- Select ticket to refund
- Choose reason from dropdown:
  - Can no longer attend
  - Event cancelled
  - Event rescheduled
  - Other
- Optional comment field
- "Submit Request" button
- Refund policy reminder
- Track refund status

---

### Organizer Pages

#### Organizations List
- Cards showing:
  - Organization logo
  - Name
  - Role (Owner, Admin, Member, etc.)
  - Number of events
  - Total tickets sold
- "Create New Organization" button
- Tap card to view organization dashboard

#### Create Organization
- Organization name
- Slug (auto-generated, editable)
- Upload logo
- Website URL
- Description
- Default currency selection
- "Create Organization" button

#### Organization Dashboard
- Welcome header with organization name
- Quick stats:
  - Total events
  - Total tickets sold
  - Total revenue
  - Active team members
- Recent events list
- Quick actions:
  - Create Event
  - View Team
  - Financial Dashboard
  - Settings
- Subscription plan badge (Free, Starter, Pro, Enterprise)

#### Events List
- Filter: All, Published, Draft, Closed, Archived
- Sort: Date, Name, Sales
- Event cards with:
  - Cover image thumbnail
  - Event name and date
  - Status badge
  - Tickets sold / total
  - Revenue
- "Create Event" FAB (floating action button)
- Tap card to view event dashboard

#### Create Event (Multi-Step Form)

**Step 1: Basic Information**
- Event name (required)
- Slug (auto-generated from name)
- Category dropdown (Music, Sports, Conference, etc.)
- Event type: In-person, Online, Hybrid
- Description rich text editor
- "AI Assistance" button to generate description
- Cover image upload (drag & drop or select)
- Image preview with crop tool

**Step 2: Date & Location**
- Start date picker
- Start time picker
- End date picker
- End time picker
- Timezone selection
- For in-person/hybrid:
  - Venue name
  - Street address
  - City, State, Country
  - Map with location pin
  - Drag map to adjust location
- For online/hybrid:
  - Meeting link (Zoom, Teams, etc.)

**Step 3: Ticket Types**
- "Add Ticket Type" button
- For each ticket type:
  - Name (VIP, Regular, Early Bird, etc.)
  - Description
  - Price and currency
  - Total quantity
  - Sales start date/time (optional)
  - Sales end date/time (optional)
  - Min/max tickets per order
  - Active toggle
- Drag to reorder ticket types
- Duplicate ticket type button
- Delete ticket type button
- At least one ticket type required

**Step 4: Customization**
- Checkout questions builder:
  - Add question button
  - Question types: Text, Email, Phone, Dropdown, Checkbox
  - Mark as required toggle
  - Reorder questions
- Event branding:
  - Primary color picker
  - Logo upload (separate from organization logo)
  - Email header image
- Social preview:
  - Preview how event appears when shared
  - Edit meta title and description

**Step 5: Review & Publish**
- Preview of complete event page
- "Save as Draft" button
- "Publish Event" button
- Success modal with:
  - Event published message
  - Event URL
  - "View Event" button
  - "Share Event" button
  - "Go to Dashboard" button

#### Event Dashboard (Stats & Bookings)
- Event header: image, name, date, status
- Key metrics cards:
  - Tickets sold / total capacity
  - Revenue (gross and net)
  - Conversion rate
  - Views
- Sales chart (line graph over time)
- Ticket type performance (pie chart)
- Recent bookings list:
  - Attendee name
  - Ticket type
  - Quantity
  - Amount paid
  - Timestamp
- Quick actions:
  - Edit Event
  - View Attendees
  - Check-In
  - Share Event
  - Export Reports

#### Edit Event
- Same multi-step form as Create Event
- Pre-filled with existing data
- "Save Changes" button
- Warning if event already has bookings
- Cannot change: slug, organization

#### Manage Ticket Types
- List of all ticket types
- Inline editing:
  - Change price
  - Update quantity
  - Toggle active/inactive
  - Modify sales dates
- Add new ticket type
- Reorder ticket types
- Cannot delete ticket type with existing sales
- Real-time sales count per ticket type

#### Checkout Questions Setup
- List of current questions
- Add question button
- Edit question inline
- Reorder via drag handles
- Delete question
- Question types: Short text, Long text, Email, Phone, Number, Dropdown, Multi-select, Checkbox
- Required toggle
- Preview mode showing attendee view

#### Coupons Management
- List of active and expired coupons
- Create coupon form:
  - Code (unique, uppercase)
  - Discount type: Percentage or Fixed amount
  - Discount value
  - Apply to: All tickets or Specific ticket types
  - Usage limits: Total uses, per-user limit
  - Expiration date
  - Active toggle
- Usage statistics:
  - Times used
  - Total discount given
  - Revenue impact
- Deactivate/delete coupon

#### Event Customization (Branding)
- Primary color picker
- Secondary color picker
- Logo upload
- Banner image upload
- Custom CSS (enterprise only)
- Email template customization:
  - Ticket email
  - Reminder email
  - Thank you email
  - Variables available: {attendee_name}, {event_name}, {ticket_type}, etc.
- Preview emails

#### Analytics Dashboard (Charts & Graphs)
- Date range selector (last 7 days, 30 days, all time, custom)
- Export as PDF button
- **Sales Overview:**
  - Total revenue (line chart)
  - Tickets sold over time (area chart)
  - Average order value
- **Ticket Performance:**
  - Sales by ticket type (bar chart)
  - Remaining inventory (gauge charts)
- **Payment Methods:**
  - Payment method distribution (pie chart)
  - Success vs. failed payments
- **Geographic Data:**
  - Attendees by country/city (map)
  - Top locations table
- **Traffic Sources:**
  - Referral sources (direct, social, affiliate)
  - Campaign performance
- **Demographics:**
  - Age distribution (if collected)
  - Gender distribution (if collected)

#### Attendee List
- Search by name, email, or booking reference
- Filter by:
  - Ticket type
  - Check-in status (checked in, not checked in)
  - Payment status
- Columns:
  - Attendee name
  - Email
  - Phone
  - Ticket type
  - Booking reference
  - Check-in status
  - Actions (view details, check in manually, send email)
- Bulk actions:
  - Export selected
  - Send bulk email
  - Bulk check-in
- Pagination

#### Export Reports
- Report types:
  - Attendee list (CSV, Excel, PDF)
  - Sales report (CSV, Excel)
  - Financial report (PDF)
  - Check-in report (CSV, PDF)
- Date range selection
- Include/exclude fields selection
- "Generate Report" button
- Download or email report

#### Check-In Dashboard
- Event header with date/time
- Total stats:
  - Expected attendees
  - Checked in
  - Not checked in
  - Check-in percentage (progress bar)
- "Download Attendee List" button (for offline mode)
- Offline mode indicator (green = synced, yellow = pending sync)
- "Open Scanner" button
- Real-time check-in activity feed:
  - Timestamp
  - Attendee name
  - Ticket type
  - Checked in by (team member)
- Filter by ticket type

#### QR Scanner for Check-In
- Full-screen camera view
- QR code scanning reticle
- Flash toggle button
- Manual entry button (for camera issues)
- Scan feedback:
  - **Success:** Green screen, attendee name, ticket type, checkmark animation, success sound
  - **Already checked in:** Orange screen, "Already checked in at [time]", warning sound
  - **Invalid ticket:** Red screen, "Invalid ticket", error sound, reason (refunded, wrong event, expired)
- Check-in counter at top
- "Close Scanner" button

#### Manual Check-In
- Search field (name, email, booking reference)
- Search results list
- Tap attendee to view details
- "Check In" button
- Confirmation modal
- Success feedback

#### Financial Dashboard
- Current balance (available for withdrawal)
- Pending balance (24hr hold after event)
- Total earnings (all time)
- Platform fees paid
- Revenue breakdown by event
- Withdrawal status section
- "Request Withdrawal" button
- Payment method on file (mobile money number)
- Update payout details

#### Withdrawal Requests
- Request withdrawal form:
  - Amount (max = available balance)
  - Mobile money provider (MTN, Orange)
  - Mobile money number
  - Confirm number
- Withdrawal fee estimate
- Net amount to receive
- "Submit Request" button
- Confirmation modal

#### Withdrawal History
- List of all withdrawals
- Status: Pending, Approved, Completed, Failed
- Details per withdrawal:
  - Amount
  - Fee
  - Net received
  - Date requested
  - Date completed
  - Transaction ID
  - Mobile money number (masked)
- Download receipt

#### Refund Management
- List of refund requests
- Filter by: Pending, Approved, Denied, Processed
- Refund cards showing:
  - Attendee name and email
  - Event name
  - Ticket type
  - Amount to refund
  - Reason
  - Date requested
- "Review" button

#### Refund Processing
- Refund details modal:
  - Attendee information
  - Ticket details
  - Refund amount
  - Reason and comment
  - Original payment method
- Actions:
  - Approve full refund
  - Approve partial refund (enter amount)
  - Deny refund (enter reason)
- Confirmation step
- Auto-process on approval (via payment gateway)
- Email notification to attendee

#### Team Management
- List of team members with:
  - Profile photo
  - Name
  - Email
  - Role
  - Date joined
  - Invited by
  - Actions (edit role, remove)
- Pending invitations section
- "Invite Member" button

#### Invite Members
- Email input (multiple emails separated by comma)
- Role selection dropdown
- Custom message (optional)
- "Send Invitation" button
- Invitation preview
- Pending invitations list:
  - Email
  - Role
  - Date sent
  - Actions (resend, cancel)

#### Affiliate Links
- "Create Affiliate Link" button
- Affiliate link generator:
  - Affiliate name/label
  - Commission type (percentage or fixed)
  - Commission rate
  - Generate unique code
- Active affiliate links list:
  - Link URL (copy button)
  - Clicks
  - Conversions
  - Revenue generated
  - Commission earned
  - Status (active/inactive)
- Affiliate leaderboard
- Payout management

#### Message Campaigns
- "Create Campaign" button
- Campaign types:
  - Email
  - SMS (enterprise)
  - Push notification
- Campaign form:
  - Campaign name
  - Subject line (for email)
  - Message body (rich text editor for email, plain text for SMS)
  - Recipient selection:
    - All attendees
    - Specific ticket types
    - Checked-in attendees only
    - Not checked-in attendees
  - Schedule: Send now or Schedule for later
- Preview message
- "Send Campaign" button

#### Campaign Analytics
- List of sent campaigns
- Campaign cards showing:
  - Name
  - Type (email, SMS, push)
  - Date sent
  - Recipients count
  - Open rate (email)
  - Click rate
  - Conversion rate
- Tap for detailed analytics:
  - Delivery status
  - Opens over time (chart)
  - Link click tracking
  - Unsubscribes

---

### AI Features Pages

#### AI Assistant Chat
- Chat interface (WhatsApp-style)
- Message input with voice button
- User messages (right-aligned, blue bubble)
- AI responses (left-aligned, gray bubble)
- Suggested quick actions as chips
- Context awareness (current event being viewed)
- "Clear Chat" button
- Chat history persistence

#### AI Content Generator
- Content type selector:
  - Event Description
  - Social Media Post (Twitter, Facebook, Instagram)
  - Email Campaign
  - Tagline/Slogan
- Input fields:
  - Event name
  - Category
  - Key details (optional)
- Tone selector: Professional, Casual, Exciting, Formal
- Language selector
- "Generate Content" button
- Generated content display (editable)
- "Regenerate" button for variations
- "Copy" button
- "Use This Content" button (inserts into event form)

#### AI Sales Prediction
- Select event from dropdown
- Date range for prediction
- "Generate Prediction" button
- Results display:
  - Predicted tickets sold (with confidence range)
  - Predicted revenue
  - Sales velocity chart
  - Peak sales periods
  - Comparison with similar events
- Recommendations section
- Export prediction report

#### AI Pricing Optimization
- Event selector
- Current pricing display
- "Analyze Pricing" button
- Results:
  - Recommended price range per ticket type
  - Price elasticity chart
  - Competitor pricing (if available)
  - Revenue impact scenarios (lower price = more sales, higher price = more revenue)
- Strategy recommendations:
  - Early bird pricing
  - Dynamic pricing suggestions
  - Bundle deals
- "Apply Recommendations" button (updates ticket prices)

#### AI Marketing Strategy
- Event selector
- Target audience inputs (optional)
- Budget (optional)
- "Generate Strategy" button
- Strategy sections:
  - Target audience profile
  - Recommended channels (social media, email, affiliates, paid ads)
  - Content themes
  - Campaign timeline (countdown to event)
  - Budget allocation
  - Expected ROI
- Download strategy as PDF
- Add tasks to campaign planner

#### Support Tickets List
- List of support tickets
- Status filter: Open, In Progress, Resolved, Closed
- Priority badges: Low, Medium, High, Urgent
- Ticket cards showing:
  - Subject
  - Category (Technical, Billing, Refund, General)
  - Status
  - Priority
  - Date created
  - Last update
- "Create New Ticket" button
- Search tickets

#### Create Support Ticket
- Category dropdown
- Subject line
- Description (rich text)
- Attach screenshots/files
- Priority selection
- "Submit Ticket" button
- Auto-categorization via AI
- Suggested solution articles (before submitting)

#### Ticket Detail/Conversation
- Ticket header: subject, status, priority, ID
- Conversation thread (chronological)
- Staff responses with timestamp and name
- User replies
- AI-suggested responses (for staff)
- Status change log
- "Reply" button
- Attach files button
- "Close Ticket" button (if resolved)
- Rating prompt on close (1-5 stars)

---

### Settings & Notifications

#### Notification Center
- Tabs: All, Unread
- Notifications grouped by date (Today, Yesterday, This Week, Earlier)
- Notification types:
  - Ticket purchased
  - Event reminder
  - Payment received
  - Refund request
  - Team invitation
  - Campaign sent
  - System announcements
- Tap to view details
- Swipe to delete
- Mark all as read
- Auto-expire old notifications

#### Notification Preferences
- Toggle each notification type:
  - Purchase confirmations
  - Event reminders (1 day before, 1 hour before)
  - Organizer updates
  - Marketing emails
  - Sales notifications (for organizers)
  - Team activity
  - Payment status
- Delivery method per type:
  - Push notification
  - Email
  - SMS (enterprise)
- Quiet hours (do not disturb)
- Notification sound selection

#### Theme Selection (Light/Dark)
- Theme options:
  - Light mode (preview)
  - Dark mode (preview)
  - System default (auto switch)
- Live preview of selected theme
- Apply button

#### Language Selection
- List of supported languages:
  - English
  - French
  - Spanish
  - Portuguese
  - Swahili
  - More...
- Search languages
- Select and apply
- App restarts to apply language

#### AI Features Toggle
- Master toggle (enable/disable all AI)
- Individual feature toggles:
  - AI Assistant
  - Content Generator
  - Sales Prediction
  - Pricing Optimization
  - Marketing Strategy
  - Auto-categorization
- Data usage notice
- Privacy settings for AI

#### Security Settings
- Change password
- Two-factor authentication (2FA):
  - Enable/disable
  - Setup: SMS or Authenticator app
  - Backup codes
- Active sessions:
  - List of logged-in devices
  - Location and last active
  - "Log out device" button
- Login history
- "Log out all devices" button
- Delete account (requires password confirmation)

---

### Navigation

#### Bottom Tab Bar (Primary Navigation)
- **Home Tab:**
  - Icon: Home
  - Destination: Event discovery/browse page

- **Tickets Tab:**
  - Icon: Ticket
  - Destination: My Tickets list
  - Badge: Number of upcoming tickets

- **Create/Manage Tab:**
  - Icon: Plus circle (for regular users) or Dashboard (for organizers)
  - For regular users: Quick create event
  - For organizers: Organization dashboard

- **AI Tab:**
  - Icon: Sparkles/Star
  - Destination: AI Assistant chat

- **Profile Tab:**
  - Icon: User avatar
  - Destination: User profile
  - Red dot for unread notifications

#### Side Drawer (Organizer Features)
- Opened by hamburger menu icon
- Sections:
  - **My Organizations:**
    - List of organizations user belongs to
    - Switch organization
  - **Events:**
    - All Events
    - Create Event
  - **Analytics:**
    - Dashboard
    - Reports
  - **Financial:**
    - Financial Dashboard
    - Withdrawals
    - Refunds
  - **Marketing:**
    - Campaigns
    - Affiliates
    - Coupons
  - **Team:**
    - Team Members
    - Invite Members
  - **Settings:**
    - Organization Settings
    - App Settings
  - **Help & Support:**
    - Help Center
    - Contact Support
    - What's New

#### Search Interface
- Global search bar in top app bar
- Search types:
  - Events (by name, organizer, location)
  - Organizations
  - Categories
- Search suggestions as you type
- Recent searches
- Clear history
- Voice search button
- Barcode scanner (for quick ticket lookup)

---

## Technical Implementation

### API Architecture
- **Base URL:** `https://api.reckot.com/v1/`
- **Authentication:** JWT tokens (access + refresh)
- **Content Type:** JSON
- **Rate Limiting:** 1000 requests/hour per user

### Key API Endpoints

**Authentication:**
- `POST /auth/register` - Create account
- `POST /auth/login` - Login
- `POST /auth/otp/send` - Send OTP
- `POST /auth/otp/verify` - Verify OTP
- `POST /auth/password/reset` - Request password reset
- `POST /auth/refresh` - Refresh access token

**Events:**
- `GET /events` - List all events (with filters)
- `GET /events/{slug}` - Get event details
- `POST /events` - Create event
- `PUT /events/{id}` - Update event
- `DELETE /events/{id}` - Delete event
- `POST /events/{id}/publish` - Publish event

**Tickets:**
- `GET /events/{event_id}/tickets` - Get ticket types
- `POST /bookings` - Create booking
- `GET /bookings/{reference}` - Get booking details
- `GET /my-tickets` - User's tickets
- `POST /tickets/{id}/transfer` - Transfer ticket

**Payments:**
- `POST /payments/initiate` - Start payment
- `GET /payments/{id}/status` - Check payment status
- `POST /payments/webhook` - Payment gateway webhook

**Refunds:**
- `POST /refunds/request` - Request refund
- `GET /refunds` - List refunds
- `PUT /refunds/{id}/approve` - Approve refund
- `PUT /refunds/{id}/deny` - Deny refund

**Organizations:**
- `GET /organizations` - List user's organizations
- `POST /organizations` - Create organization
- `GET /organizations/{id}/members` - List team members
- `POST /organizations/{id}/invite` - Invite member

**Check-In:**
- `GET /events/{id}/attendees` - Download attendee list
- `POST /checkin` - Check in attendee
- `POST /checkin/sync` - Sync offline check-ins

**AI:**
- `POST /ai/chat` - Chat with AI assistant
- `POST /ai/generate-content` - Generate content
- `POST /ai/predict-sales` - Sales prediction
- `POST /ai/optimize-pricing` - Pricing optimization

**Analytics:**
- `GET /events/{id}/analytics` - Event analytics
- `GET /organizations/{id}/analytics` - Organization analytics

### Real-Time Features
- **WebSocket Connection:** `wss://api.reckot.com/ws`
- **Channels:**
  - `event.{event_id}.sales` - Real-time sales updates
  - `event.{event_id}.checkins` - Real-time check-in updates
  - `user.{user_id}.notifications` - User notifications

### Offline Functionality
- **Local Storage:**
  - Tickets (with QR codes) cached for offline access
  - Downloaded attendee lists encrypted with AES-256
  - User profile and settings
- **Sync Queue:**
  - Check-ins queued locally if offline
  - Auto-sync when connection restored
  - Conflict resolution (server wins)

### Security
- HTTPS/TLS encryption for all API calls
- JWT tokens expire after 1 hour (refresh tokens valid for 30 days)
- QR codes encrypted with unique booking reference
- Check-in data encrypted at rest
- Payment data never stored on device
- PCI DSS compliance for card payments
- 2FA support (SMS and TOTP)

### Platform Requirements
- **iOS:** 14.0 or later (iPhone, iPad)
- **Android:** 8.0 (Oreo) or later
- **Permissions:**
  - Camera (for QR scanning)
  - Location (for nearby events, optional)
  - Storage (for ticket PDFs, offline data)
  - Push notifications
  - Biometric (for biometric login)

### Suggested Tech Stack
- **Framework:** React Native or Flutter
- **State Management:** Redux (React Native) or Provider/Riverpod (Flutter)
- **HTTP Client:** Axios (React Native) or Dio (Flutter)
- **Local Database:** SQLite or Realm
- **QR Code:** react-native-qrcode-svg or qr_flutter
- **Camera:** react-native-camera or camera (Flutter)
- **Maps:** react-native-maps or google_maps_flutter
- **Charts:** react-native-chart-kit or fl_chart
- **Push Notifications:** Firebase Cloud Messaging
- **Analytics:** Firebase Analytics or Mixpanel

---

## Organization Subscription Plans

### Free Plan (2% service fee)
- 2 events per month
- 100 tickets per event
- Basic analytics (CSV export only)
- Standard support
- No custom branding
- No flyer generator
- No advanced analytics

### Starter Plan (5% service fee)
- 10 events per month
- 500 tickets per event
- Advanced analytics (CSV, Excel, PDF export)
- Standard support
- AI-powered flyer generator
- No custom branding

### Pro Plan (3% service fee)
- Unlimited events
- Unlimited tickets
- Advanced analytics (CSV, Excel, PDF, JSON export)
- Priority support
- AI-powered flyer generator
- Custom branding (colors, logo, white-label)
- Advanced campaign features

### Enterprise Plan (Custom service fee, negotiable)
- Everything in Pro
- Custom service fee (can be 0%)
- Dedicated account manager
- On-site support
- SLA guarantee
- API access
- Custom integrations
- Multi-organization management

---

## Success Metrics & KPIs

**For Users (Attendees):**
- Time to complete ticket purchase < 2 minutes
- Payment success rate > 95%
- App store rating > 4.5 stars
- User retention rate > 60% after 30 days

**For Organizers:**
- Event creation time < 10 minutes
- Average tickets sold per event: 100+
- Check-in time per attendee < 5 seconds
- Organizer satisfaction score > 4.7/5

**Platform Metrics:**
- Monthly active users (MAU)
- Total events created
- Total tickets sold
- Gross merchandise value (GMV)
- Platform fee revenue
- Average order value
- Conversion rate (event views to ticket purchases)

---

## Accessibility Features
- VoiceOver/TalkBack support
- Dynamic text sizing
- High contrast mode
- Color blind friendly color schemes
- Keyboard navigation support
- Screen reader optimized labels
- Haptic feedback for important actions
- Clear error messages and instructions

---

## Localization
- Multi-language support (English, French, Spanish, Portuguese, Swahili)
- Right-to-left (RTL) layout support for Arabic (future)
- Local date/time formats
- Currency formatting per locale
- Phone number formatting by country
- Address formats by region

---

## Future Enhancements
- Apple Wallet / Google Pay integration for tickets
- In-app chat between attendees and organizers
- Live streaming integration for online events
- Merchandise sales at events
- Seat selection for venue events
- Early access ticket tiers (presale)
- NFT tickets (blockchain-based)
- Loyalty program (rewards points)
- Event recommendations via machine learning
- Advanced fraud detection
- Multi-currency support for single event
- Subscription-based event series
