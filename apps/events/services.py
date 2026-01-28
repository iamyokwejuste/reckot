from .forms import EventForm

def create_event(user, organization, data):
    form = EventForm(data)
    if form.is_valid():
        event = form.save(commit=False)
        event.organization = organization
        event.save()
        return event, None
    return None, form.errors
