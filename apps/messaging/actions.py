from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from apps.orgs.models import Organization, Membership
from apps.events.models import Event
from apps.messaging.models import MessageTemplate, MessageCampaign, MessageDelivery
from apps.messaging.services import prepare_campaign, track_open, track_click
from apps.messaging.tasks import send_campaign_task


class CampaignListView(LoginRequiredMixin, View):
    def get(self, request, org_slug):
        org = get_object_or_404(Organization, slug=org_slug)
        if not Membership.objects.filter(organization=org, user=request.user).exists():
            return redirect('orgs:list')

        campaigns = MessageCampaign.objects.filter(organization=org).select_related('event')
        return render(request, 'messaging/campaign_list.html', {
            'organization': org,
            'campaigns': campaigns,
        })


class CampaignCreateView(LoginRequiredMixin, View):
    def get(self, request, org_slug, event_slug):
        org = get_object_or_404(Organization, slug=org_slug)
        event = get_object_or_404(Event, organization=org, slug=event_slug)
        templates = MessageTemplate.objects.filter(organization=org)
        ticket_types = event.ticket_types.all()

        return render(request, 'messaging/campaign_create.html', {
            'organization': org,
            'event': event,
            'templates': templates,
            'ticket_types': ticket_types,
        })

    def post(self, request, org_slug, event_slug):
        org = get_object_or_404(Organization, slug=org_slug)
        event = get_object_or_404(Event, organization=org, slug=event_slug)

        campaign = MessageCampaign.objects.create(
            organization=org,
            event=event,
            name=request.POST.get('name'),
            message_type=request.POST.get('message_type'),
            subject=request.POST.get('subject', ''),
            body=request.POST.get('body'),
            recipient_filter=request.POST.get('recipient_filter'),
            ticket_types=request.POST.getlist('ticket_types'),
            created_by=request.user,
        )

        if request.POST.get('send_now'):
            prepare_campaign(campaign)
            send_campaign_task.enqueue(campaign.id)
            messages.success(request, _('Campaign is being sent.'))
        else:
            messages.success(request, _('Campaign saved as draft.'))

        return redirect('messaging:campaign_detail', org_slug=org_slug, campaign_ref=campaign.reference)


class CampaignDetailView(LoginRequiredMixin, View):
    def get(self, request, org_slug, campaign_ref):
        org = get_object_or_404(Organization, slug=org_slug)
        campaign = get_object_or_404(MessageCampaign, reference=campaign_ref, organization=org)
        deliveries = campaign.deliveries.all()[:100]

        return render(request, 'messaging/campaign_detail.html', {
            'organization': org,
            'campaign': campaign,
            'deliveries': deliveries,
        })


class CampaignSendView(LoginRequiredMixin, View):
    def post(self, request, org_slug, campaign_ref):
        org = get_object_or_404(Organization, slug=org_slug)
        campaign = get_object_or_404(MessageCampaign, reference=campaign_ref, organization=org)

        if campaign.status == MessageCampaign.Status.DRAFT:
            prepare_campaign(campaign)
            send_campaign_task.enqueue(campaign.id)
            messages.success(request, _('Campaign is being sent.'))
        else:
            messages.error(request, _('Campaign cannot be sent.'))

        return redirect('messaging:campaign_detail', org_slug=org_slug, campaign_ref=campaign.reference)


class TemplateListView(LoginRequiredMixin, View):
    def get(self, request, org_slug):
        org = get_object_or_404(Organization, slug=org_slug)
        templates = MessageTemplate.objects.filter(organization=org)

        return render(request, 'messaging/template_list.html', {
            'organization': org,
            'templates': templates,
        })


class TemplateCreateView(LoginRequiredMixin, View):
    def get(self, request, org_slug):
        org = get_object_or_404(Organization, slug=org_slug)
        return render(request, 'messaging/template_create.html', {
            'organization': org,
        })

    def post(self, request, org_slug):
        org = get_object_or_404(Organization, slug=org_slug)

        MessageTemplate.objects.create(
            organization=org,
            name=request.POST.get('name'),
            template_type=request.POST.get('template_type'),
            subject=request.POST.get('subject', ''),
            body=request.POST.get('body'),
            created_by=request.user,
        )

        messages.success(request, _('Template created.'))
        return redirect('messaging:template_list', org_slug=org_slug)


class TrackOpenView(View):
    def get(self, request, tracking_id):
        track_open(tracking_id)
        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        return HttpResponse(pixel, content_type='image/gif')


class TrackClickView(View):
    def get(self, request, tracking_id):
        track_click(tracking_id)
        redirect_url = request.GET.get('url', '/')
        return redirect(redirect_url)
