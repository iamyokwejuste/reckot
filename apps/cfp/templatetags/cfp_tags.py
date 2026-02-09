from django import template

register = template.Library()


STATUS_COLORS = {
    "DRAFT": "muted",
    "SUBMITTED": "primary",
    "UNDER_REVIEW": "warning",
    "ACCEPTED": "success",
    "REJECTED": "destructive",
    "WAITLISTED": "warning",
    "WITHDRAWN": "muted",
    "CONFIRMED": "success",
    "OPEN": "success",
    "CLOSED": "destructive",
    "REVIEWING": "warning",
    "DECIDED": "primary",
}


@register.filter
def cfp_status_color(status):
    """Return the color variant for a CFP/proposal status."""
    return STATUS_COLORS.get(status, "muted")


@register.filter
def star_range(value):
    """Return a range for star rating display."""
    try:
        return range(1, 6)
    except (TypeError, ValueError):
        return range(1, 6)


@register.filter
def filled_stars(value):
    """Return the number of filled stars for a rating."""
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return 0
