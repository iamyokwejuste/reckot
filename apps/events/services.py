from apps.events.forms import EventForm


def create_event(user, organization, data, files=None):
    form = EventForm(data, files)
    if form.is_valid():
        event = form.save(commit=False)
        event.organization = organization
        event.save()
        return event, None
    return None, form.errors
