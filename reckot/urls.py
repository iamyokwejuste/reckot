from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import JsonResponse
from apps.core.actions import (
    HomeView, WhyUsView, PrivacyView, TermsView, FeaturesView,
    OTPVerificationView, ResendOTPView, robots_txt, service_worker
)
from apps.core.sitemaps import StaticViewSitemap, HomeSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'home': HomeSitemap,
}

def health_check(request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sw.js', service_worker, name='service_worker'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('', HomeView.as_view(), name='home'),
    path('features/', FeaturesView.as_view(), name='features'),
    path('why-us/', WhyUsView.as_view(), name='why_us'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('admin/', admin.site.urls),
    path('events/', include('apps.events.urls')),
    path('orgs/', include('apps.orgs.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('payments/', include('apps.payments.urls')),
    path('checkin/', include('apps.checkin.urls')),
    path('reports/', include('apps.reports.urls')),
    path('messaging/', include('apps.messaging.urls')),
    path('widgets/', include('apps.widgets.urls')),
    path('m/', include('apps.marketing.urls')),
    path('app/', include('apps.core.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/verify-email/', OTPVerificationView.as_view(), name='otp_verify'),
    path('accounts/resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
