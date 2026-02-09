from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.views.static import serve
from django.views.generic import RedirectView

from apps.core.views.actions import (
    HomeView,
    WhyUsView,
    PrivacyView,
    TermsView,
    FeaturesView,
    HealthCheckView,
    OTPVerificationView,
    ResendOTPView,
    robots_txt,
    service_worker,
    manifest_view,
    PhoneLoginRequestView,
    PhoneLoginVerifyView,
    PhoneSignupRequestView,
    PhoneSignupVerifyView,
)
from apps.core.utils.sitemaps import StaticViewSitemap, HomeSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "home": HomeSitemap,
}

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("health/", HealthCheckView.as_view(), name="health_check"),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico", permanent=True),
    ),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sw.js", service_worker, name="service_worker"),
    path("site.webmanifest", manifest_view, name="manifest"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", HomeView.as_view(), name="home"),
    path("features/", FeaturesView.as_view(), name="features"),
    path("why-us/", WhyUsView.as_view(), name="why_us"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("terms/", TermsView.as_view(), name="terms"),
    path("admin/reports/", include("apps.analytics.urls")),
    path("admin/", admin.site.urls),
    path("events/", include("apps.events.urls")),
    path("orgs/", include("apps.orgs.urls")),
    path("tickets/", include("apps.tickets.urls")),
    path("payments/", include("apps.payments.urls")),
    path("checkin/", include("apps.checkin.urls")),
    path("reports/", include("apps.reports.urls")),
    path("messaging/", include("apps.messaging.urls")),
    path("widgets/", include("apps.widgets.urls")),
    path("m/", include("apps.marketing.urls")),
    path("ai/", include("apps.ai.urls")),
    path("cfp/", include("apps.cfp.urls")),
    path("app/", include("apps.core.urls")),
    path("accounts/", include("allauth.urls")),
    path("accounts/verify-email/", OTPVerificationView.as_view(), name="otp_verify"),
    path("accounts/resend-otp/", ResendOTPView.as_view(), name="resend_otp"),
    path(
        "accounts/phone/login/",
        PhoneLoginRequestView.as_view(),
        name="phone_login_request",
    ),
    path(
        "accounts/phone/login/verify/",
        PhoneLoginVerifyView.as_view(),
        name="phone_login_verify",
    ),
    path(
        "accounts/phone/signup/",
        PhoneSignupRequestView.as_view(),
        name="phone_signup_request",
    ),
    path(
        "accounts/phone/signup/verify/",
        PhoneSignupVerifyView.as_view(),
        name="phone_signup_verify",
    ),
]

urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

handler400 = "apps.core.views.views.handler400"
handler403 = "apps.core.views.views.handler403"
handler404 = "apps.core.views.views.handler404"
handler500 = "apps.core.views.views.handler500"
