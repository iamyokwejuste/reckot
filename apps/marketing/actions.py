from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from apps.marketing.models import AffiliateLink, SocialShare
from apps.marketing.services import track_affiliate_click, track_social_share, get_share_urls
from apps.events.models import Event


class AffiliateRedirectView(View):
    def get(self, request, code):
        link = track_affiliate_click(code)
        if not link:
            return redirect('home')

        request.session['affiliate_code'] = code

        if link.event:
            return redirect('events:detail', org_slug=link.event.organization.slug, event_slug=link.event.slug)

        return redirect('orgs:detail', slug=link.organization.slug)


class TrackShareView(View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        platform = request.POST.get('platform', SocialShare.Platform.COPY_LINK)

        user = request.user if request.user.is_authenticated else None
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        if ip:
            ip = ip.split(',')[0].strip()

        track_social_share(event, platform, user, ip)

        return JsonResponse({'success': True})


class ShareUrlsView(View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        base_url = request.build_absolute_uri('/').rstrip('/')
        urls = get_share_urls(event, base_url)
        return JsonResponse(urls)
