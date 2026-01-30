import logging
from apps.events.forms import EventForm

logger = logging.getLogger(__name__)


def create_event(user, organization, data, files=None):
    form = EventForm(data, files)
    if form.is_valid():
        try:
            event = form.save(commit=False)
            event.organization = organization
            event.save()
            return event, None
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return None, {"__all__": [f"Failed to create event: {str(e)}"]}
    logger.warning(f"Event form validation failed: {form.errors}")
    return None, form.errors
