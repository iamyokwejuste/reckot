from django.shortcuts import redirect, get_object_or_404, render
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from apps.marketing.models import AffiliateLink, AffiliateConversion, SocialShare
from apps.marketing.services import (
    track_affiliate_click,
    track_social_share,
    get_share_urls,
)
from apps.events.models import Event
from apps.orgs.models import Organization


class AffiliateRedirectView(View):
    def get(self, request, code):
        link = track_affiliate_click(code)
        if not link:
            return redirect("home")

        request.session["affiliate_code"] = code

        if link.event:
            return redirect(
                "events:detail",
                org_slug=link.event.organization.slug,
                event_slug=link.event.slug,
            )

        return redirect("orgs:detail", slug=link.organization.slug)


class TrackShareView(View):
    def post(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        platform = request.POST.get("platform", SocialShare.Platform.COPY_LINK)

        user = request.user if request.user.is_authenticated else None
        ip = request.META.get(
            "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")
        )
        if ip:
            ip = ip.split(",")[0].strip()

        track_social_share(event, platform, user, ip)

        return JsonResponse({"success": True})


class ShareUrlsView(View):
    def get(self, request, org_slug, event_slug):
        event = get_object_or_404(Event, organization__slug=org_slug, slug=event_slug)
        base_url = request.build_absolute_uri("/").rstrip("/")
        urls = get_share_urls(event, base_url)
        return JsonResponse(urls)


class AffiliateListView(LoginRequiredMixin, View):
    def get(self, request, org_slug):
        org = get_object_or_404(Organization, slug=org_slug, members=request.user)

        links = (
            AffiliateLink.objects.filter(organization=org)
            .annotate(
                conversion_count=Count("conversions"),
                total_commission=Sum("conversions__commission_amount"),
            )
            .order_by("-created_at")
        )

        stats = {
            "total_links": links.count(),
            "active_links": links.filter(is_active=True).count(),
            "total_clicks": links.aggregate(total=Sum("clicks"))["total"] or 0,
            "total_conversions": AffiliateConversion.objects.filter(
                affiliate_link__organization=org
            ).count(),
        }

        return render(
            request,
            "marketing/affiliate_list.html",
            {
                "organization": org,
                "links": links,
                "stats": stats,
            },
        )


class AffiliateCreateView(LoginRequiredMixin, View):
    def get(self, request, org_slug):
        org = get_object_or_404(Organization, slug=org_slug, members=request.user)
        events = Event.objects.filter(organization=org, state=Event.State.PUBLISHED)

        return render(
            request,
            "marketing/affiliate_create.html",
            {
                "organization": org,
                "events": events,
            },
        )

    def post(self, request, org_slug):
        org = get_object_or_404(Organization, slug=org_slug, members=request.user)

        event_id = request.POST.get("event")
        event = None
        if event_id:
            event = get_object_or_404(Event, id=event_id, organization=org)

        AffiliateLink.objects.create(
            organization=org,
            event=event,
            name=request.POST.get("name"),
            commission_type=request.POST.get("commission_type", "PERCENTAGE"),
            commission_value=request.POST.get("commission_value", 0),
        )

        return redirect("marketing:affiliate_list", org_slug=org_slug)


class AffiliateDetailView(LoginRequiredMixin, View):
    def get(self, request, org_slug, link_code):
        org = get_object_or_404(Organization, slug=org_slug, members=request.user)
        link = get_object_or_404(AffiliateLink, code=link_code, organization=org)

        conversions = link.conversions.select_related("booking__event").order_by(
            "-created_at"
        )[:50]

        return render(
            request,
            "marketing/affiliate_detail.html",
            {
                "organization": org,
                "link": link,
                "conversions": conversions,
            },
        )

    def post(self, request, org_slug, link_code):
        org = get_object_or_404(Organization, slug=org_slug, members=request.user)
        link = get_object_or_404(AffiliateLink, code=link_code, organization=org)

        action = request.POST.get("action")
        if action == "toggle":
            link.is_active = not link.is_active
            link.save(update_fields=["is_active"])
        elif action == "delete":
            link.delete()
            return redirect("marketing:affiliate_list", org_slug=org_slug)

        return redirect(
            "marketing:affiliate_detail", org_slug=org_slug, link_code=link_code
        )
