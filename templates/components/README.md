# Reckot Slippers Components

This directory contains reusable Slippers components for the Reckot application.

## New Components (February 2026)

### 1. kpi_card
**Purpose:** Display KPI metrics with title, value, and optional trend information
**Files using this pattern:** 3 admin analytics templates (6+ occurrences)

**Parameters:**
- `title` (required) - The KPI label
- `value` (required) - The metric value to display
- `trend_text` (optional) - Trend description (e.g., "Last 90 days")
- `icon` (optional) - Lucide icon name
- `color` (optional) - CSS color for the value text
- `attrs` (optional) - Additional HTML attributes

**Example:**
```django
{% load slippers %}

{% #kpi_card
    title="Total Revenue"
    value="$12,450.00"
    trend_text="Last 90 days"
    icon="trending-up"
    color="rgb(var(--color-primary-600))" %}
{% /kpi_card %}
```

---

### 2. stat_card
**Purpose:** Dashboard statistic cards with icon and optional progress bar
**Files using this pattern:** 17+ templates (17+ occurrences)

**Parameters:**
- `label` (required) - The stat label/title
- `value` (required) - The metric value
- `icon` (required) - Lucide icon name
- `description` (optional) - Small subtitle text
- `color_variant` (optional) - Color theme: primary, emerald, blue, amber (default: primary)
- `hover_color` (optional) - Hover border color (default: primary/50)
- `progress_percent` (optional) - Progress bar width percentage
- `attrs` (optional) - Additional HTML attributes

**Example:**
```django
{% #stat_card
    label="Total Tickets"
    value="1,247"
    description="Confirmed tickets sold"
    icon="ticket"
    color_variant="emerald"
    progress_percent=75 %}
{% /stat_card %}
```

---

### 3. alert_banner
**Purpose:** Full-width alert/notification banners with icons
**Files using this pattern:** 10+ templates

**Parameters:**
- `variant` (optional) - Alert type: error, success, warning, info (default: info)
- `title` (optional) - Alert title
- `message` (optional) - Alert message text
- `icon` (optional) - Override default icon
- `is_dismissible` (optional) - Add close button (boolean)
- `attrs` (optional) - Additional HTML attributes
- `children` - Can use slot for complex content

**Example:**
```django
{% #alert_banner variant="success" title="Success!" message="Your event was created successfully." is_dismissible=True %}{% /alert_banner %}

<!-- Or with slot: -->
{% #alert_banner variant="error" %}
    <p>There were errors with your submission:</p>
    <ul>
        <li>Invalid email address</li>
        <li>Password too short</li>
    </ul>
{% /alert_banner %}
```

---

### 4. feature_list_item
**Purpose:** List items with icons for feature lists
**Files using this pattern:** features.html (18+ occurrences)

**Parameters:**
- `title` (optional) - Feature title
- `description` (optional) - Feature description
- `icon` (optional) - Lucide icon (default: check)
- `icon_color` (optional) - Color variant: emerald, blue, amber (default: emerald)
- `attrs` (optional) - Additional HTML attributes
- `children` - Can use slot for custom content

**Example:**
```django
<ul class="space-y-3">
    {% #feature_list_item
        title="MTN MoMo integration"
        description="Instant payment confirmation across all MoMo-supported countries" %}
    {% /feature_list_item %}

    {% #feature_list_item
        title="SMS notifications"
        description="Automatic ticket delivery via SMS"
        icon="message-circle"
        icon_color="blue" %}
    {% /feature_list_item %}
</ul>
```

---

### 5. feature_card
**Purpose:** Feature boxes with icon, title, and description
**Files using this pattern:** features.html (6+ occurrences)

**Parameters:**
- `icon` (required) - Lucide icon name
- `title` (optional) - Feature title
- `description` (optional) - Feature description
- `icon_bg_color` (optional) - Icon background color (default: foreground)
- `icon_text_color` (optional) - Icon color (default: background)
- `animation_class` (optional) - Animation classes (e.g., "animate-scale delay-1")
- `animation_once` (optional) - Animation runs once (default: true)
- `attrs` (optional) - Additional HTML attributes
- `children` - Can use slot for custom content

**Example:**
```django
{% #feature_card
    icon="users"
    title="Team collaboration"
    description="Add unlimited team members with custom permissions"
    animation_class="animate-scale delay-1" %}
{% /feature_card %}
```

---

### 6. activity_item
**Purpose:** Timeline/activity feed items
**Files using this pattern:** reports/dashboard.html

**Parameters:**
- `title` (required) - Activity title
- `description` (optional) - Activity description
- `time` (optional) - Time stamp text
- `type` (optional) - Activity type: sale, checkin, refund, warning, info (default: info)
- `icon` (optional) - Override default icon based on type
- `attrs` (optional) - Additional HTML attributes

**Example:**
```django
{% #activity_item
    title="New ticket sale"
    description="John Doe purchased 2 VIP tickets"
    time="2 mins ago"
    type="sale" %}
{% /activity_item %}

{% #activity_item
    title="Guest checked in"
    description="Jane Smith - VIP ticket #12345"
    time="5 mins ago"
    type="checkin" %}
{% /activity_item %}
```

---

### 7. export_option
**Purpose:** Export format selection cards (for modals/forms)
**Files using this pattern:** attendee_list.html (4+ occurrences)

**Parameters:**
- `title` (required) - Format title (e.g., "Excel", "PDF")
- `description` (optional) - Format description
- `icon` (required) - Lucide icon name
- `color_variant` (optional) - Color scheme: green, red, blue, primary (default: primary)
- `is_form` (optional) - Whether this is a form button (default: false)
- `form_action` (optional) - Form action URL (if is_form=true)
- `form_fields` (optional) - Hidden form fields HTML
- `href` (optional) - Link href (if is_form=false)
- `attrs` (optional) - Additional HTML attributes

**Example:**
```django
<!-- As a form button -->
{% #export_option
    title="Excel"
    description="Microsoft Excel spreadsheet"
    icon="table"
    color_variant="green"
    is_form=True
    form_action="/export/excel/" %}
    <input type="hidden" name="format" value="xlsx">
{% /export_option %}

<!-- As a link -->
{% #export_option
    title="PDF"
    description="Portable Document Format"
    icon="file-text"
    color_variant="red"
    href="/export/pdf/" %}
{% /export_option %}
```

---

### 8. card_table
**Purpose:** Card wrapper for data tables with optional title/icon
**Files using this pattern:** dashboard.html (3+ occurrences)

**Parameters:**
- `title` (optional) - Section title
- `icon` (optional) - Section icon
- `empty_message` (optional) - Message when no data
- `col_span` (optional) - Grid column span class (e.g., "lg:col-span-2")
- `attrs` (optional) - Additional HTML attributes
- `children` - Table HTML content (slot)

**Example:**
```django
{% #card_table
    title="Revenue by Ticket Type"
    icon="coins"
    col_span="lg:col-span-2"
    empty_message="No revenue data available" %}
    <table class="w-full">
        <thead>
            <tr>
                <th>Ticket Type</th>
                <th>Sold</th>
                <th>Revenue</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>VIP</td>
                <td>50</td>
                <td>$5,000</td>
            </tr>
        </tbody>
    </table>
{% /card_table %}
```

---

## Component Priority & Usage

| Component | Priority | Occurrences | Status |
|-----------|----------|-------------|--------|
| kpi_card | High | 6+ | ✅ Created |
| stat_card | High | 17+ | ✅ Updated |
| alert_banner | High | 10+ | ✅ Created |
| feature_list_item | Medium | 18+ | ✅ Created |
| feature_card | Medium | 6+ | ✅ Created |
| activity_item | Medium | Multiple | ✅ Created |
| export_option | Medium | 4+ | ✅ Created |
| card_table | Low-Medium | 3+ | ✅ Created |

## Next Steps

To refactor existing templates to use these components:

1. Search for repetitive patterns in templates
2. Replace with component syntax: `{% #component_name param="value" %}`
3. Test to ensure styling and functionality remain identical
4. Update cache version after template changes

## Example Refactor

**Before:**
```html
<div class="kpi-card">
    <div class="kpi-title">Total Revenue</div>
    <div class="kpi-value" style="color: rgb(var(--color-primary-600));">
        $12,450.00
    </div>
    <div class="kpi-trend">Last 90 days</div>
</div>
```

**After:**
```django
{% #kpi_card
    title="Total Revenue"
    value="$12,450.00"
    trend_text="Last 90 days"
    color="rgb(var(--color-primary-600))" %}
{% /kpi_card %}
```

## Notes

- All components use Lucide icons (`data-lucide` attributes)
- Components follow the design system color tokens (primary, emerald, blue, amber, red)
- Most components support `attrs` parameter for additional HTML attributes
- Components use Slippers' `{{ children }}` for slot content where appropriate
