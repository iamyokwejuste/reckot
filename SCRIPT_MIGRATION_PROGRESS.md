# Script Migration Progress

## Overview
Moving 33+ embedded scripts from HTML templates to external JavaScript files and Stimulus controllers.

## Completed ✅

### 1. ReckotApp Core Application Logic
- **From:** `templates/partials/scripts.html` (inline script, ~113 lines)
- **To:** `/static/js/reckot-app.js`
- **Status:** ✅ Complete
- **Description:** Main application initialization, HTMX event handling, Lucide icon management, and toast notification system

### 2. AI Insights Controller
- **From:** `templates/reports/_ai_insights.html` (inline script, ~88 lines)
- **To:** `/static/js/controllers/ai-insights_controller.js`
- **Status:** ✅ Complete
- **Description:** Stimulus controller for AI insights generation with API calls, state management, and error handling

### 3. Payment Select Controller
- **From:** `templates/payments/select_method.html` (inline script, ~50 lines)
- **To:** `/static/js/controllers/payment-select_controller.js`
- **Status:** ✅ Controller created, template update pending
- **Description:** Stimulus controller for payment method selection and carrier detection (MTN/Orange)

## In Progress 🚧

### 4. Payment Select Template Update
- **Status:** Template needs controller references added
- **Next:** Add `data-controller="payment-select"` and targets/actions to form elements

## Pending High Priority 📋

### 5. Refund Request Controller
- **From:** `templates/payments/refunds/request.html` (~16 lines)
- **To:** `/static/js/controllers/refund-request_controller.js`
- **Description:** Toggle partial refund amount field based on refund type selection

### 6. Chart Theme Script
- **From:** `templates/components/chart_theme.html` (~46 lines)
- **To:** `/static/js/chart-theme.js`
- **Description:** ChartJS theme management with dark mode support

### 7. Datepicker Initialization
- **From:** `templates/partials/datepicker_init.html` (~101 lines)
- **To:** `/static/js/datepicker-init.js`
- **Description:** Flatpickr initialization with MutationObserver for dynamic elements

### 8. Flyer Generator Utils
- **From:** `templates/events/flyer_generator.html` (~57 lines)
- **To:** `/static/js/flyer-generator.js`
- **Description:** Utility functions for CSRF token, image preview, error handling, and share API

### 9. Walkthrough Controller
- **From:** `templates/components/ai_walkthrough.html` (~300 lines)
- **To:** `/static/js/controllers/walkthrough_controller.js`
- **Description:** AI onboarding walkthrough system with 8-step guided tour

### 10. Flyer Editor Controller
- **From:** `templates/events/flyer_config.html` (~207 lines)
- **To:** `/static/js/controllers/flyer-editor_controller.js`
- **Description:** Template image handling, photo positioning/resizing, text field management, drag-and-drop

## Pending Medium Priority 📝

### 11. Organization Create Form Persistence
- **From:** `templates/orgs/create.html` (~15 lines)
- **Description:** Form auto-save functionality using FormPersistence

### 12. Messaging Template Clipboard
- **From:** `templates/messaging/template_list.html` (~18 lines)
- **Description:** Copy to clipboard with visual feedback

### 13. Bulk Invite File Handling
- **From:** `templates/orgs/bulk_invite.html` (~16 lines)
- **Description:** CSV file name display and clear functionality

### 14. Checkin Service Worker
- **From:** `templates/checkin/verify.html` (~13 lines)
- **Description:** Service worker registration for offline check-ins

## Cleanup Tasks 🧹

### Redundant Code to Remove
1. **templates/orgs/edit.html** (lines 149-153) - Redundant Lucide initialization
2. **templates/reports/_live_stats.html** (lines 90-95) - Redundant Lucide initialization

### Theme Initialization Consolidation
- **Affected files:** `base.html`, `layouts/dashboard.html`, `admin/base_site.html`
- **Task:** Consolidate duplicated theme detection/initialization code into single source
- **Approach:** Create `theme-init.js` or use Stimulus controller

## Files That Stay As-Is ✓

1. **templates/events/edit_event.html** - Only loads external scripts ✓
2. **templates/events/create_event.html** - Only loads external scripts ✓
3. **templates/events/discover.html** - Only JSON data embedding ✓
4. **templates/payments/_pending.html** - Small Motion.js animation (8 lines) ✓

## Next Steps

1. Complete payment-select template update
2. Create refund-request controller
3. Extract chart-theme.js
4. Extract datepicker-init.js
5. Register all new controllers in stimulus-app.js
6. Update version timestamp
7. Test all functionality

## Controller Registration

After creating all controllers, add to `/static/js/stimulus-app.js`:
```javascript
{ name: 'ai-insights', path: 'ai-insights_controller.js' },
{ name: 'payment-select', path: 'payment-select_controller.js' },
{ name: 'refund-request', path: 'refund-request_controller.js' },
{ name: 'walkthrough', path: 'walkthrough_controller.js' },
{ name: 'flyer-editor', path: 'flyer-editor_controller.js' },
```

## Notes
- All Stimulus controllers use ESM imports from CDN
- CSRF token extraction is standardized across controllers
- Lucide icon re-initialization handled by ReckotApp globally
- Dark mode/theme logic needs consolidation to avoid duplication
