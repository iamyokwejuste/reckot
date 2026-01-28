from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from apps.core.actions import HomeView, WhyUsView, PrivacyView, TermsView, FeaturesView, OTPVerificationView, ResendOTPView
from apps.core.sitemaps import StaticViewSitemap, HomeSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'home': HomeSitemap,
}


def robots_txt(request):
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    sitemap_url = f"{scheme}://{host}/sitemap.xml"
    content = f"""# Reckot Robots.txt
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /accounts/
Disallow: /payments/
Disallow: /checkin/

Sitemap: {sitemap_url}
"""
    return HttpResponse(content, content_type="text/plain")


urlpatterns = [
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('', HomeView.as_view(), name='home'),
    path('features/', FeaturesView.as_view(), name='features'),
    path('why-us/', WhyUsView.as_view(), name='why_us'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('admin/', admin.site.urls),
    path('events/', include('apps.events.urls')),
    path('orgs/', include('apps.orgs.urls')),
    path('payments/', include('apps.payments.urls')),
    path('checkin/', include('apps.checkin.urls')),
    path('reports/', include('apps.reports.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/verify-email/', OTPVerificationView.as_view(), name='otp_verify'),
    path('accounts/resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
