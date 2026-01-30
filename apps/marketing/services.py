from django.utils import timezone
from apps.marketing.models import AffiliateLink, AffiliateConversion, SocialShare


def track_affiliate_click(code):
    try:
        link = AffiliateLink.objects.get(code=code, is_active=True)
        if link.expires_at and link.expires_at < timezone.now():
            return None
        link.clicks += 1
        link.save(update_fields=["clicks"])
        return link
    except AffiliateLink.DoesNotExist:
        return None


def create_affiliate_conversion(affiliate_code, booking):
    try:
        link = AffiliateLink.objects.get(code=affiliate_code, is_active=True)

        if link.event and link.event != booking.event:
            return None

        commission = link.calculate_commission(booking.total_amount)

        conversion = AffiliateConversion.objects.create(
            affiliate_link=link,
            booking=booking,
            order_amount=booking.total_amount,
            commission_amount=commission,
        )
        return conversion
    except AffiliateLink.DoesNotExist:
        return None


def track_social_share(event, platform, user=None, ip_address=None):
    SocialShare.objects.create(
        event=event,
        platform=platform,
        user=user,
        ip_address=ip_address,
    )


def get_share_urls(event, base_url):
    event_url = f"{base_url}/events/{event.organization.slug}/{event.slug}/"
    title = event.title
    description = event.description[:100] if event.description else ""

    return {
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={event_url}",
        "twitter": f"https://twitter.com/intent/tweet?text={title}&url={event_url}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={event_url}",
        "whatsapp": f"https://wa.me/?text={title}%20{event_url}",
        "telegram": f"https://t.me/share/url?url={event_url}&text={title}",
        "email": f"mailto:?subject={title}&body={description}%0A%0A{event_url}",
    }
