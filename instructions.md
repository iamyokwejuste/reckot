# MASTER PROMPT

**RECKOT — Event Management Platform**
*(Django 6+, Slippers, Tailwind-only, HTMX, scale-ready)*

---

## Role & Objective

You are a **senior fullstack engineer (2026 standards)** building **Reckot**, a production-grade **event management platform**.

The system must be:

* Calm, reliable, and boring in the best way
* Server-rendered first
* Optimized for **200,000+ users/records**
* Easy to reason about and maintain
* Built without frontend over-engineering

This is a **Django monolith**, not a SPA.

---

## Core Technology Stack

* Django 6+
* Django Slippers (server-side UI components)
* Tailwind CSS (utilities only)
* HTMX (interactions)
* Alpine.js (only for local UI state)
* PostgreSQL
* Django Tasks (built-in framework, not Celery)
* `uv` as the Python package manager
* Lucide icons via CDN

---

## HARD RULES (NON-NEGOTIABLE)

### Styling & UI

* **NO CSS files**
* **NO inline `<style>`**
* **NO gradients**
* **NO emojis**
* **NO npm installs**
* **ALL styling via Tailwind utilities**
* **All colors via Tailwind theme tokens**
* shadcn-inspired design system, ported to Django Slippers

Tailwind must define:

* Brand colors (uniform, solid)
* Neutral palette
* Spacing scale
* Radii
* Typography
* Shadows

Accessibility is mandatory (semantic HTML, keyboard navigation, WCAG AA contrast).

---

### Icons

* **Lucide icons via CDN only**
* No SVGs committed
* No icon fonts
* No static icon assets
* Icons rendered via `data-lucide`
* Styled only with Tailwind classes

Example:

```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<script>
  lucide.createIcons()
</script>

<i data-lucide="check" class="w-4 h-4 text-muted"></i>
```

---

### Code Discipline

* **No comments**
* **No docstrings**
* **No markdown files**
* **Files must not exceed 200 lines**
* Follow **DRY principles**
* Use clear, consistent naming for:

  * classes
  * variables
  * functions
* No hidden magic
* No unnecessary abstractions

---

### Performance & Scale (Critical)

At **every coding decision**, ask:

> “Will this still be optimal with 200,000 records?”

Rules:

* No Python loops over large querysets
* Always prefer DB-side filtering
* Use indexes
* Use `select_related` / `prefetch_related`
* Paginate aggressively
* Cursor pagination where appropriate

---

### Search (Explicit Constraint)

* **NO Elasticsearch**
* **NO external search engines**
* Use PostgreSQL only:

  * indexed fields
  * `SearchVector`
  * trigram similarity where useful

Search must be fast, explainable, and predictable.

---

## Project Structure (Starter)

```text
reckot/
  manage.py
  pyproject.toml
  uv.lock

  reckot/
    settings.py
    urls.py
    asgi.py
    wsgi.py

  apps/
    core/
    orgs/
    events/
    tickets/
    payments/
    checkin/
    reports/

  components/
    Button/
    Input/
    Card/
    Modal/
    Table/
    StatusPill/
    EmptyState/
    LoadingState/

  templates/
    base.html
    layouts/
    partials/

  static/
    js/
      htmx.min.js
      alpine.min.js
```

Notes:

* `static/` is **not** for icons
* Lucide is always CDN-loaded
* Components live only under `components/`

---

## Platform Capabilities (Must Be Implemented)

### Organizations & Roles

* Organization creation
* Admin and staff roles
* Scoped permissions

---

### Events

* Metadata: title, description, date/time, location
* Capacity rules
* States:

  * Draft
  * Published
  * Closed
  * Archived

---

### Ticketing

* Single tickets
* Group tickets
* Ticket types per event
* Capacity enforcement
* Unique ticket codes
* Ticket PDF sent via email

---

### Payments

* Local payments with **3 fallback methods**
* Support:

  * MTN MoMo
  * Orange Money
* Payment states:

  * Pending
  * Confirmed
  * Failed
  * Expired
* Idempotent confirmation
* Payment confirmation triggers:

  * Ticket generation
  * Invoice generation
  * Email delivery

---

### Invoices

* Automatic PDF invoices
* Include:

  * Organization
  * Attendee
  * Ticket breakdown
  * Payment method
* Sent via email

---

### Check-In & Swag

* Check-in via:

  * Email link
  * Unique ticket code
* Prevent double check-in
* Swag tracking:

  * Admin-configurable
  * Mark collected during check-in
  * Stored per attendee

---

### Imports & Invitations

* Import email lists
* Assign by:

  * Event
  * Ticket type
* Send **unique payment links**
* Track states:

  * Invited
  * Paid
  * Pending
  * Expired

---

### Reports & Exports

* Export:

  * RSVPs
  * Payments
  * Swag collection
* CSV / Excel
* Mask emails by default

---

## Architecture Rules

### Backend

* `models.py` → data only
* `queries.py` → read logic
* `services.py` → write logic
* `actions.py` → HTTP + HTMX entry points
* `tasks.py` → background work

No business logic in:

* templates
* components
* views

---

### Frontend

* Django Slippers components only
* Tailwind utilities only
* Components:

  * accept explicit props
  * no DB access
  * no side effects

---

## Slippers Component Library (Required)

Generate reusable components:

* Button (variants)
* Input / Textarea
* Card
* Alert
* Badge
* Table
* Modal
* Tabs
* Status Pill
* Empty State
* Loading State

Each component:

* `.html` + `.py`
* Tailwind utilities only
* Accessible
* Under 200 lines

---

## HTMX Interaction Blueprints

For each major feature, define:

* action in `actions.py`
* service invocation
* partial template
* HTMX attributes

Cover:

* Ticket purchase
* Payment confirmation
* Live search
* Check-in flow
* Group ticket allocation
* Export generation

No client-side business logic.

---

## Django Tasks (Correct Usage)

Use **Django’s built-in Tasks framework (Django 6)**.

Understand:

* Django provides the **task API**
* A backend/worker is required to execute tasks in production

### Task Definition Example

```python
from django.tasks import task

@task
def send_ticket_email(ticket_id: int):
    from apps.tickets.services import deliver_ticket_pdf
    deliver_ticket_pdf(ticket_id)
```

### Enqueue from Service Layer

```python
send_ticket_email.enqueue(ticket.id)
```

Tasks must be:

* Idempotent
* Retry-safe
* Short-running where possible

---

## Task Runner Setup

* Configure Django Tasks backend
* Use database-backed or minimal worker approach
* Document how tasks are executed in production
* No Celery usage

---

## Output Expectations

When generating code, always:

1. Keep files under 200 lines
2. Use Tailwind-only styling
3. Use Lucide icons via CDN
4. Optimize queries for scale
5. Avoid unnecessary abstractions
6. Maintain clean naming
7. Respect DRY

---

## Final Instruction

Optimize for:

* Maintainability
* Predictability
* Performance at scale
* Calm, consistent UX

Avoid:

* CSS files
* Gradients
* Frontend maximalism
* Clever but fragile abstractions

Build **Reckot** as a system that feels obvious, stable, and fast.


# CONTINUATION — SAMPLE PAYMENT → CHECK-IN FLOW (RECKOT)

## 0. Base includes (once, in `base.html`)

```html
<script src="https://unpkg.com/htmx.org@1.9.12"></script>
<script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>

<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<script>
  document.addEventListener("DOMContentLoaded", () => lucide.createIcons())
</script>

<script src="https://unpkg.com/motion@10.18.0/dist/motion.min.js"></script>
```

`motion` here = **Framer Motion One (official Framer team)**.
This is the correct tool.

---

## 1. Payment button (Slippers component)

### `components/Button/Button.html`

```html
<button
  type="{{ type|default:'button' }}"
  class="
    inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium
    bg-brand text-brand-foreground
    hover:bg-brand/90
    disabled:opacity-50
  "
  {{ attrs }}
>
  {{ children }}
</button>
```

---

## 2. Payment initiation (HTMX)

### Payment CTA (template)

```html
<div
  id="payment-panel"
  hx-post="{% url 'payments:start' event_id %}"
  hx-trigger="click"
  hx-target="#payment-panel"
  hx-swap="outerHTML"
  hx-indicator="#payment-loader"
>
  {% component "Button" %}
    <i data-lucide="credit-card" class="w-4 h-4"></i>
    Pay Now
  {% endcomponent %}
</div>

<div id="payment-loader" class="hidden text-sm text-muted">
  Processing payment…
</div>
```

No JS.
HTMX owns the state.

---

## 3. Payment action (server)

### `apps/payments/actions.py`

```python
from django.http import HttpResponse
from apps.payments.services import start_payment

def start(request, event_id):
    payment = start_payment(request.user, event_id)
    return HttpResponse(
        render_payment_pending(payment),
        headers={"HX-Trigger": "payment-started"}
    )
```

---

## 4. Payment pending partial (animated with Framer)

### `templates/payments/_pending.html`

```html
<div
  id="payment-status"
  class="rounded-md border p-4 text-sm"
  hx-get="{% url 'payments:poll' payment.id %}"
  hx-trigger="every 3s"
  hx-target="#payment-status"
  hx-swap="outerHTML"
  data-motion
>
  <div class="flex items-center gap-2">
    <i data-lucide="loader" class="w-4 h-4 animate-spin"></i>
    Waiting for payment confirmation…
  </div>
</div>

<script>
  motion.animate(
    "[data-motion]",
    { opacity: [0, 1], y: [8, 0] },
    { duration: 0.25 }
  )
</script>
```

Framer Motion One runs **after HTMX swap**.
No React. No state bugs.

---

## 5. Payment polling (optimized)

### `apps/payments/actions.py`

```python
from django.http import HttpResponse
from apps.payments.queries import get_payment_status

def poll(request, payment_id):
    status = get_payment_status(payment_id)
    if status.confirmed:
        return HttpResponse(render_payment_success(status))
    return HttpResponse(render_payment_pending(status))
```

Queries must use indexed fields only.

---

## 6. Payment success → ticket issued

### `templates/payments/_success.html`

```html
<div
  class="rounded-md border p-4 text-sm"
  data-motion
>
  <div class="flex items-center gap-2 text-success">
    <i data-lucide="check-circle" class="w-4 h-4"></i>
    Payment confirmed. Ticket sent by email.
  </div>

  <a
    href="{% url 'checkin:verify' ticket.code %}"
    class="mt-3 inline-block text-brand underline"
  >
    Go to check-in
  </a>
</div>

<script>
  motion.animate(
    "[data-motion]",
    { opacity: [0, 1], scale: [0.98, 1] },
    { duration: 0.25 }
  )
</script>
```

---

## 7. Check-in screen (code or email link)

### `apps/checkin/actions.py`

```python
from django.shortcuts import render
from apps.checkin.services import verify_ticket

def verify(request, code):
    result = verify_ticket(code)
    return render(request, "checkin/result.html", result)
```

---

## 8. Check-in result (with swag)

### `templates/checkin/result.html`

```html
<div
  class="max-w-md rounded-md border p-6"
  data-motion
>
  {% if valid %}
    <div class="flex items-center gap-2 text-success">
      <i data-lucide="badge-check" class="w-5 h-5"></i>
      Checked in successfully
    </div>

    {% if swag %}
      <div class="mt-3 text-sm">
        Swag collected: {{ swag }}
      </div>
    {% endif %}
  {% else %}
    <div class="flex items-center gap-2 text-destructive">
      <i data-lucide="x-circle" class="w-5 h-5"></i>
      Invalid or already used ticket
    </div>
  {% endif %}
</div>

<script>
  motion.animate(
    "[data-motion]",
    { opacity: [0, 1], y: [6, 0] },
    { duration: 0.2 }
  )
</script>
```

---

## Why this flow is **correct**

* HTMX owns **state transitions**
* Django owns **truth**
* Tailwind owns **visual language**
* Lucide owns **icons**
* Framer Motion One owns **micro-interactions**
* No JS state
* No hydration
* No race conditions
* No CSS files
* Scales cleanly
* Debuggable HTML

This is exactly how **modern server-driven UIs are built in 2026**.

---

# PROJECT UPDATES & REFINEMENTS

The following rules and guidelines have been added to refine the project architecture and coding standards.

## Theming

*   **Color Palette:** The `tailwind.config.js` must define a comprehensive color palette including:
    *   `primary`: The main brand color.
    *   `secondary`: A color for less prominent elements.
    *   `destructive`: A color for actions that have destructive consequences (e.g., delete).
*   **Dark Mode:** Dark mode must be supported and should be triggered by the user's system preference (`prefers-color-scheme`).

## Role-Based Access Control (RBAC) & Invitations

*   **Permissions:** A granular permission system must be implemented to control user access to specific resources and actions within an organization.
*   **Invitations:** A system for inviting users to an organization must be implemented. This should include generating unique invitation links and tracking their status.
*   **Role Model:** Roles are not hardcoded. A `Role` model must be used to dynamically define roles for each organization. The `Membership` and `Invitation` models should have a `ForeignKey` to this `Role` model.

## Views

*   **Class-Based Views:** All views must be implemented as class-based views, inheriting from `django.views.View` or other generic class-based views. Function-based views are not allowed.

## Code Style

*   **No Comments/Docstrings:** The "no comments" and "no docstrings" rule is strictly enforced. Code should be self-documenting through clear naming and structure.

## Application Importing

*   **App Module Structure:** The `apps` directory is a Python package. All applications reside within this package.
*   **`INSTALLED_APPS`:** Apps must be registered in `INSTALLED_APPS` using the `apps.<app_name>` format (e.g., `'apps.core'`).
*   **Imports:** All imports to app modules must use the full path from the project root (e.g., `from apps.core.models import User`). The `sys.path` should not be modified.

