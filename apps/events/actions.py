import uuid

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone

from apps.events.forms import EventForm, TicketTypeForm
from apps.events.services import create_event
from apps.events.queries import get_user_events
from apps.events.models import Event, Coupon, EventFlyerConfig, FlyerTextField
from apps.events.flyer_service import generate_flyer
from apps.orgs.models import Organization
from apps.tickets.forms import BookingForm
from apps.tickets.services import create_booking
from apps.tickets.models import Ticket, Booking
from apps.payments.models import Payment


class PublicEventListView(View):
    def get(self, request):
        events = Event.objects.filter(
            is_public=True,
            state=Event.State.PUBLISHED
        ).select_related('organization').order_by('-start_at')

        search = request.GET.get('q', '')
        if search:
            events = events.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )

        location = request.GET.get('location', '')
        if location:
            events = events.filter(location__icontains=location)

        paginator = Paginator(events, 12)
        page = request.GET.get('page', 1)
        events = paginator.get_page(page)

        return render(request, 'events/discover.html', {
            'events': events,
            'search': search,
            'location': location,
        })


class PublicEventDetailView(View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related('organization'),
            organization__slug=org_slug,
            slug=event_slug,
            state=Event.State.PUBLISHED
        )
        ticket_types = event.ticket_types.filter(is_active=True)
        checkout_questions = event.checkout_questions.all()

        affiliate_code = request.session.get('affiliate_code')

        return render(request, 'events/public_detail.html', {
            'event': event,
            'ticket_types': ticket_types,
            'checkout_questions': checkout_questions,
            'affiliate_code': affiliate_code,
        })


class EventListView(LoginRequiredMixin, View):
    def get(self, request):
        events = get_user_events(request.user)
        return render(request, 'events/list_events.html', {'events': events})

class EventCreateView(LoginRequiredMixin, View):
    def get(self, request):
        organizations = Organization.objects.filter(members=request.user)
        if not organizations.exists():
            return render(request, 'events/no_org.html')
        form = EventForm()
        return render(request, 'events/create_event.html', {
            'form': form,
            'organizations': organizations,
        })

    def post(self, request):
        organizations = Organization.objects.filter(members=request.user)
        if not organizations.exists():
            return render(request, 'events/no_org.html')

        org_id = request.POST.get('organization')
        organization = get_object_or_404(Organization, id=org_id, members=request.user)

        event, errors = create_event(request.user, organization, request.POST, request.FILES)
        if event:
            return redirect('events:detail', org_slug=organization.slug, event_slug=event.slug)
        else:
            form = EventForm(request.POST, request.FILES)
            return render(request, 'events/create_event.html', {
                'form': form,
                'organizations': organizations,
                'errors': errors
            })

class TicketTypeManageView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        ticket_types = event.ticket_types.all()
        form = TicketTypeForm()
        return render(request, 'events/manage_ticket_types.html', {'event': event, 'ticket_types': ticket_types, 'form': form})

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        form = TicketTypeForm(request.POST)
        if form.is_valid():
            ticket_type = form.save(commit=False)
            ticket_type.event = event
            ticket_type.save()
            return redirect('events:manage_ticket_types', org_slug=org_slug, event_slug=event_slug)
        ticket_types = event.ticket_types.all()
        return render(request, 'events/manage_ticket_types.html', {'event': event, 'ticket_types': ticket_types, 'form': form})


class EventDetailView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        booking_form = BookingForm(initial={'ticket_type': event.ticket_types.first()})
        return render(request, 'events/event_detail.html', {'event': event, 'booking_form': booking_form})

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        booking_form = BookingForm(request.POST)
        if booking_form.is_valid():
            ticket_type = booking_form.cleaned_data['ticket_type']
            quantity = booking_form.cleaned_data['quantity']
            booking, error = create_booking(request.user, ticket_type, quantity)
            if booking:
                return redirect('events:list')
            else:
                return render(request, 'events/event_detail.html', {'event': event, 'booking_form': booking_form, 'error': error})
        return render(request, 'events/event_detail.html', {'event': event, 'booking_form': booking_form})


class EventDashboardView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related('organization'),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user
        )

        bookings = Booking.objects.filter(event=event)
        tickets = Ticket.objects.filter(booking__event=event)

        tickets_sold = tickets.count()
        checked_in = tickets.filter(checked_in=True).count()
        checkin_rate = (checked_in / tickets_sold * 100) if tickets_sold > 0 else 0

        revenue = Payment.objects.filter(
            booking__event=event,
            status=Payment.Status.CONFIRMED
        ).aggregate(total=Sum('amount'))['total'] or 0

        stats = {
            'tickets_sold': tickets_sold,
            'checked_in': checked_in,
            'checkin_rate': checkin_rate,
            'revenue': revenue,
        }

        return render(request, 'events/event_dashboard.html', {
            'event': event,
            'stats': stats,
            'is_published': event.state == Event.State.PUBLISHED,
            'manage_tickets_url': reverse('events:manage_ticket_types', args=[org_slug, event_slug]),
            'checkin_url': reverse('checkin:dashboard', args=[org_slug, event_slug]),
            'export_url': reverse('reports:export_center', args=[org_slug, event_slug]),
            'analytics_url': reverse('reports:dashboard', args=[org_slug, event_slug]),
            'flyer_config_url': reverse('events:flyer_config', args=[org_slug, event_slug]),
        })


class ApplyFeatureView(LoginRequiredMixin, View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event,
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user
        )

        if not event.is_public:
            return redirect('events:dashboard', org_slug=org_slug, event_slug=event_slug)

        if event.is_featured:
            return redirect('events:dashboard', org_slug=org_slug, event_slug=event_slug)

        event.feature_requested_at = timezone.now()
        event.feature_rejection_reason = ''
        event.save(update_fields=['feature_requested_at', 'feature_rejection_reason'])

        return redirect('events:dashboard', org_slug=org_slug, event_slug=event_slug)


class CouponListView(LoginRequiredMixin, View):
    def get(self, request):
        coupons = Coupon.objects.filter(
            organization__members=request.user
        ).select_related('organization', 'event').annotate(
            usage_count=Count('usages')
        ).order_by('-created_at')

        stats = {
            'total': coupons.count(),
            'active': coupons.filter(is_active=True).count(),
        }

        return render(request, 'events/coupons/list.html', {
            'coupons': coupons,
            'stats': stats,
        })


class CouponCreateView(LoginRequiredMixin, View):
    def get(self, request):
        organizations = Organization.objects.filter(members=request.user)
        events = Event.objects.filter(organization__members=request.user)
        return render(request, 'events/coupons/create.html', {
            'organizations': organizations,
            'events': events,
        })

    def post(self, request):
        org_id = request.POST.get('organization')
        organization = get_object_or_404(Organization, id=org_id, members=request.user)

        event_id = request.POST.get('event')
        event = None
        if event_id:
            event = get_object_or_404(Event, id=event_id, organization=organization)

        code = request.POST.get('code', '').strip().upper()
        if not code:
            code = uuid.uuid4().hex[:8].upper()

        existing = Coupon.objects.filter(organization=organization, code=code).exists()
        if existing:
            organizations = Organization.objects.filter(members=request.user)
            events = Event.objects.filter(organization__members=request.user)
            return render(request, 'events/coupons/create.html', {
                'organizations': organizations,
                'events': events,
                'error': 'A coupon with this code already exists in this organization.',
            })

        discount_type = request.POST.get('discount_type', 'PERCENTAGE')
        discount_value = request.POST.get('discount_value', 0)
        assignment_type = request.POST.get('assignment_type', 'PUBLIC')
        assigned_email = request.POST.get('assigned_email', '').strip()
        assigned_emails_raw = request.POST.get('assigned_emails', '').strip()
        assigned_emails = [e.strip() for e in assigned_emails_raw.split(',') if e.strip()] if assigned_emails_raw else []
        max_uses = request.POST.get('max_uses', 1)
        description = request.POST.get('description', '').strip()
        valid_from = request.POST.get('valid_from') or None
        valid_until = request.POST.get('valid_until') or None

        _ = Coupon.objects.create(
            organization=organization,
            event=event,
            code=code,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            assignment_type=assignment_type,
            assigned_email=assigned_email,
            assigned_emails=assigned_emails,
            max_uses=int(max_uses) if max_uses else 1,
            valid_from=valid_from,
            valid_until=valid_until,
            is_active=True,
            created_by=request.user,
        )

        return redirect('events:coupons')


class CouponDetailView(LoginRequiredMixin, View):
    def get(self, request, coupon_id):
        coupon = get_object_or_404(
            Coupon.objects.select_related('organization', 'event'),
            id=coupon_id,
            organization__members=request.user
        )
        usages = coupon.usages.select_related('booking__user').order_by('-used_at')[:50]
        return render(request, 'events/coupons/detail.html', {
            'coupon': coupon,
            'usages': usages,
        })


class CouponToggleView(LoginRequiredMixin, View):
    def post(self, request, coupon_id):
        coupon = get_object_or_404(
            Coupon,
            id=coupon_id,
            organization__members=request.user
        )
        coupon.is_active = not coupon.is_active
        coupon.save(update_fields=['is_active'])
        return redirect('events:coupon_detail', coupon_id=coupon.id)


class CouponDeleteView(LoginRequiredMixin, View):
    def post(self, request, coupon_id):
        coupon = get_object_or_404(
            Coupon,
            id=coupon_id,
            organization__members=request.user
        )
        coupon.delete()
        return redirect('events:coupons')


class ValidateCouponView(View):
    def post(self, request):
        code = request.POST.get('code', '').strip().upper()
        event_id = request.POST.get('event_id')
        email = request.POST.get('email', '').strip()

        if not code:
            return JsonResponse({'valid': False, 'error': 'Please enter a coupon code'})

        coupon = Coupon.objects.filter(
            Q(code=code),
            Q(event_id=event_id) | Q(event__isnull=True)
        ).first()

        if not coupon:
            return JsonResponse({'valid': False, 'error': 'Invalid coupon code'})

        if not coupon.is_valid:
            return JsonResponse({'valid': False, 'error': 'This coupon is no longer valid'})

        if email and not coupon.can_be_used_by(email):
            return JsonResponse({'valid': False, 'error': 'This coupon cannot be used with your email'})

        return JsonResponse({
            'valid': True,
            'discount_type': coupon.discount_type,
            'discount_value': float(coupon.discount_value),
            'code': coupon.code,
        })


class FlyerGeneratorView(View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related('organization'),
            organization__slug=org_slug,
            slug=event_slug,
            state=Event.State.PUBLISHED
        )

        if not event.organization.has_feature('flyer_generator'):
            return render(request, 'events/flyer_upgrade.html', {'event': event})

        try:
            config = event.flyer_config
            if not config.is_enabled:
                return render(request, 'events/flyer_disabled.html', {'event': event})
        except EventFlyerConfig.DoesNotExist:
            return render(request, 'events/flyer_disabled.html', {'event': event})

        text_fields = config.text_fields.all()

        return render(request, 'events/flyer_generator.html', {
            'event': event,
            'config': config,
            'text_fields': text_fields,
        })

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related('organization'),
            organization__slug=org_slug,
            slug=event_slug,
            state=Event.State.PUBLISHED
        )

        if not event.organization.has_feature('flyer_generator'):
            return HttpResponse('Feature not available on current plan', status=403)

        try:
            config = event.flyer_config
            if not config.is_enabled:
                return HttpResponse('Flyer generation not enabled', status=403)
        except EventFlyerConfig.DoesNotExist:
            return HttpResponse('Flyer not configured', status=404)

        user_photo = request.FILES.get('photo')
        text_values = {}
        for key, value in request.POST.items():
            if key.startswith('field_'):
                field_id = key.replace('field_', '')
                text_values[field_id] = value

        try:
            flyer_image = generate_flyer(config, user_photo, text_values)
            response = HttpResponse(flyer_image.getvalue(), content_type='image/jpeg')
            response['Content-Disposition'] = f'inline; filename="{event.slug}-flyer.jpg"'
            return response
        except Exception as e:
            return HttpResponse(f'Error generating flyer: {str(e)}', status=500)


class FlyerConfigView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related('organization'),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user
        )

        has_feature = event.organization.has_feature('flyer_generator')

        try:
            config = event.flyer_config
        except EventFlyerConfig.DoesNotExist:
            config = None

        return render(request, 'events/flyer_config.html', {
            'event': event,
            'config': config,
            'has_feature': has_feature,
            'current_plan': event.organization.current_plan,
        })

    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(
            Event.objects.select_related('organization'),
            organization__slug=org_slug,
            slug=event_slug,
            organization__members=request.user
        )

        try:
            config = event.flyer_config
        except EventFlyerConfig.DoesNotExist:
            config = EventFlyerConfig(event=event)

        config.is_enabled = request.POST.get('is_enabled') == 'on'

        if 'template_image' in request.FILES:
            config.template_image = request.FILES['template_image']

        config.photo_x = int(request.POST.get('photo_x', 50))
        config.photo_y = int(request.POST.get('photo_y', 50))
        config.photo_width = int(request.POST.get('photo_width', 200))
        config.photo_height = int(request.POST.get('photo_height', 200))
        config.photo_shape = request.POST.get('photo_shape', 'CIRCLE')
        config.photo_border_width = int(request.POST.get('photo_border_width', 0))
        config.photo_border_color = request.POST.get('photo_border_color', '#ffffff')
        config.output_width = int(request.POST.get('output_width', 1080))
        config.output_height = int(request.POST.get('output_height', 1080))
        config.save()

        config.text_fields.all().delete()
        field_labels = request.POST.getlist('field_label')
        for i, label in enumerate(field_labels):
            if not label.strip():
                continue
            FlyerTextField.objects.create(
                flyer_config=config,
                label=label,
                placeholder=request.POST.getlist('field_placeholder')[i] if i < len(request.POST.getlist('field_placeholder')) else '',
                is_required=f'field_required_{i}' in request.POST,
                order=i,
                x=int(request.POST.getlist('field_x')[i]) if i < len(request.POST.getlist('field_x')) else 0,
                y=int(request.POST.getlist('field_y')[i]) if i < len(request.POST.getlist('field_y')) else 0,
                max_width=int(request.POST.getlist('field_max_width')[i]) if i < len(request.POST.getlist('field_max_width')) else 400,
                font_size=int(request.POST.getlist('field_font_size')[i]) if i < len(request.POST.getlist('field_font_size')) else 32,
                font_color=request.POST.getlist('field_font_color')[i] if i < len(request.POST.getlist('field_font_color')) else '#ffffff',
                text_align=request.POST.getlist('field_text_align')[i] if i < len(request.POST.getlist('field_text_align')) else 'CENTER',
            )

        return redirect('events:flyer_config', org_slug=org_slug, event_slug=event_slug)