import os
import re

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.templatetags.static import static

from apps.core.models import OTPVerification, User
from apps.core.tasks import resend_otp_task, send_otp_sms_task
from apps.core.services.notifications import NotificationService
from apps.events.models import Event


def robots_txt(request):
    scheme = "https" if request.is_secure() else "http"
    host = request.get_host()
    sitemap_url = f"{scheme}://{host}/sitemap.xml"
    content = f"""User-agent: *
Allow: /

Sitemap: {sitemap_url}
"""
    return HttpResponse(content, content_type="text/plain")


def service_worker(request):
    sw_path = os.path.join(
        settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], "sw.js"
    )
    if not os.path.exists(sw_path):
        sw_path = os.path.join(settings.BASE_DIR, "static", "sw.js")
    try:
        with open(sw_path, "r") as f:
            content = f.read()
        return HttpResponse(content, content_type="application/javascript")
    except FileNotFoundError:
        return HttpResponse("", content_type="application/javascript", status=404)


def manifest_view(request):
    manifest = {
        "name": "Reckot - Event Ticketing Platform",
        "short_name": "Reckot",
        "description": "Modern event ticketing and management platform",
        "icons": [
            {
                "src": request.build_absolute_uri(static("images/favicon/android-chrome-192x192.png")),
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": request.build_absolute_uri(static("images/favicon/android-chrome-512x512.png")),
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "theme_color": "#000000",
        "background_color": "#ffffff",
        "display": "standalone",
        "start_url": "/"
    }
    return JsonResponse(manifest, content_type="application/manifest+json")


class HomeView(View):
    def get(self, request):
        featured_events = (
            Event.objects.filter(
                is_featured=True, is_public=True, state=Event.State.PUBLISHED
            )
            .select_related("organization")
            .order_by("feature_order", "-feature_approved_at")[:5]
        )

        user_has_events = False
        if request.user.is_authenticated:
            user_has_events = Event.objects.filter(
                organization__members=request.user
            ).exists()

        return render(
            request,
            "core/home.html",
            {
                "featured_events": featured_events,
                "user_has_events": user_has_events,
            },
        )


class WhyUsView(View):
    def get(self, request):
        return render(request, "core/why_us.html")


class PrivacyView(View):
    def get(self, request):
        return render(request, "core/privacy.html")


class TermsView(View):
    def get(self, request):
        return render(request, "core/terms.html")


class FeaturesView(View):
    def get(self, request):
        return render(request, "core/features.html")


class OTPVerificationView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.email_verified:
            return redirect("home")
        return render(request, "account/otp_verify.html")

    def post(self, request):
        if request.user.email_verified:
            return redirect("home")

        code = request.POST.get("otp_code", "").strip()
        if not code or len(code) != 6:
            messages.error(request, _("Please enter a valid 6-digit code."))
            return render(request, "account/otp_verify.html")

        otp = (
            OTPVerification.objects.filter(
                user=request.user, otp_type=OTPVerification.Type.EMAIL, is_used=False
            )
            .order_by("-created_at")
            .first()
        )

        if not otp:
            messages.error(
                request, _("No verification code found. Please request a new one.")
            )
            return render(request, "account/otp_verify.html")

        if otp.verify(code):
            request.user.email_verified = True
            request.user.save(update_fields=["email_verified"])
            messages.success(request, _("Email verified successfully!"))
            return redirect("home")
        elif otp.is_expired:
            messages.error(request, _("Code expired. Please request a new one."))
        elif otp.attempts >= 5:
            messages.error(request, _("Too many attempts. Please request a new code."))
        else:
            messages.error(request, _("Invalid code. Please try again."))

        return render(request, "account/otp_verify.html")


class ResendOTPView(LoginRequiredMixin, View):
    def post(self, request):
        if request.user.email_verified:
            return JsonResponse(
                {"success": False, "message": _("Email already verified")}
            )

        try:
            resend_otp_task.enqueue(request.user.id, OTPVerification.Type.EMAIL)
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Failed to resend OTP: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "message": _("Failed to send code. Please try again."),
                }
            )
        return JsonResponse(
            {"success": True, "message": _("New code sent to your email")}
        )


class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "core/settings.html",
            {
                "user": request.user,
            },
        )

    def post(self, request):
        user = request.user
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if phone:
            user.phone_number = re.sub(r"[\s\-\(\)]", "", phone)

        user.save()
        messages.success(request, _("Settings updated successfully."))
        return redirect("core:settings")


class ToggleAIFeaturesView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        user.ai_features_enabled = not user.ai_features_enabled
        user.save(update_fields=["ai_features_enabled"])
        return JsonResponse({"success": True, "enabled": user.ai_features_enabled})


class PhoneLoginRequestView(View):
    def get(self, request):
        return redirect("account_login")

    def post(self, request):
        phone = request.POST.get("phone_number", "").strip()
        if not phone:
            return HttpResponse(
                '<p class="text-sm text-red-500 mt-2">'
                + str(_("Please enter a phone number"))
                + "</p>",
                status=400,
            )

        phone = self._normalize_phone(phone)
        user = User.objects.filter(phone_number=phone).first()
        if not user:
            return HttpResponse(
                '<p class="text-sm text-red-500 mt-2">'
                + str(_("No account found with this phone number"))
                + "</p>",
                status=400,
            )

        request.session["login_phone"] = phone
        try:
            if settings.TWILIO_VERIFY_SERVICE_SID:
                send_otp_sms_task.enqueue(phone)
            else:
                otp = OTPVerification.create_for_user(user, OTPVerification.Type.PHONE)
                send_otp_sms_task.enqueue(phone, otp.code)
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Failed to send OTP SMS: {e}")
        return HttpResponse(
            '<p class="text-sm text-emerald-500 mt-2">'
            + str(_("Verification code sent!"))
            + "</p>"
        )

    def _normalize_phone(self, phone):
        return re.sub(r"[\s\-\(\)]", "", phone)


class PhoneLoginVerifyView(View):
    def get(self, request):
        return redirect("account_login")

    def post(self, request):
        phone = request.POST.get("phone_number", "").strip()
        code = request.POST.get("otp_code", "").strip()

        if not phone or not code:
            messages.error(request, _("Phone number and code are required"))
            return redirect("account_login")

        phone = self._normalize_phone(phone)
        user = User.objects.filter(phone_number=phone).first()
        if not user:
            messages.error(request, _("Invalid phone number"))
            return redirect("account_login")

        verified = False
        if settings.TWILIO_VERIFY_SERVICE_SID:
            verified = NotificationService.verify_otp_sms(phone, code)
        else:
            otp = (
                OTPVerification.objects.filter(
                    user=user, otp_type=OTPVerification.Type.PHONE, is_used=False
                )
                .order_by("-created_at")
                .first()
            )

            if not otp:
                messages.error(
                    request, _("No verification code found. Please request a new one.")
                )
                return redirect("account_login")

            if otp.verify(code):
                verified = True
            elif otp.is_expired:
                messages.error(request, _("Code expired. Please request a new one."))
                return redirect("account_login")
            elif otp.attempts >= 5:
                messages.error(
                    request, _("Too many attempts. Please request a new code.")
                )
                return redirect("account_login")

        if verified:
            user.phone_verified = True
            user.save(update_fields=["phone_verified"])
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, _("Logged in successfully!"))
            return redirect("home")

        messages.error(request, _("Invalid code. Please try again."))
        return redirect("account_login")

    def _normalize_phone(self, phone):
        return re.sub(r"[\s\-\(\)]", "", phone)


class PhoneSignupRequestView(View):
    def get(self, request):
        return redirect("account_signup")

    def post(self, request):
        phone = request.POST.get("phone_number", "").strip()
        if not phone:
            return HttpResponse(
                '<p class="text-sm text-red-500 mt-2">'
                + str(_("Please enter a phone number"))
                + "</p>",
                status=400,
            )

        phone = self._normalize_phone(phone)
        if User.objects.filter(phone_number=phone).exists():
            return HttpResponse(
                '<p class="text-sm text-red-500 mt-2">'
                + str(_("An account with this phone number already exists"))
                + "</p>",
                status=400,
            )

        request.session["signup_phone"] = phone
        try:
            if settings.TWILIO_VERIFY_SERVICE_SID:
                send_otp_sms_task.enqueue(phone)
            else:
                request.session["signup_otp"] = OTPVerification.generate_code()
                send_otp_sms_task.enqueue(phone, request.session["signup_otp"])
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Failed to send OTP SMS: {e}")
        return HttpResponse(
            '<p class="text-sm text-emerald-500 mt-2">'
            + str(_("Verification code sent!"))
            + "</p>"
        )

    def _normalize_phone(self, phone):
        return re.sub(r"[\s\-\(\)]", "", phone)


class PhoneSignupVerifyView(View):
    def get(self, request):
        return redirect("account_signup")

    def post(self, request):
        phone = request.POST.get("phone_number", "").strip()
        code = request.POST.get("otp_code", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        phone = self._normalize_phone(phone)
        stored_phone = request.session.get("signup_phone")

        if phone != stored_phone:
            messages.error(request, _("Phone number mismatch. Please start over."))
            return redirect("account_signup")

        verified = False
        if settings.TWILIO_VERIFY_SERVICE_SID:
            verified = NotificationService.verify_otp_sms(phone, code)
        else:
            stored_otp = request.session.get("signup_otp")
            if code == stored_otp:
                verified = True

        if not verified:
            messages.error(request, _("Invalid verification code"))
            return redirect("account_signup")

        if not password1 or password1 != password2:
            messages.error(request, _("Passwords do not match"))
            return redirect("account_signup")

        if len(password1) < 8:
            messages.error(request, _("Password must be at least 8 characters"))
            return redirect("account_signup")

        user = User.objects.create_user(
            username=phone, phone_number=phone, phone_verified=True, password=password1
        )

        if "signup_phone" in request.session:
            del request.session["signup_phone"]
        if "signup_otp" in request.session:
            del request.session["signup_otp"]

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, _("Account created successfully!"))
        return redirect("home")

    def _normalize_phone(self, phone):
        return re.sub(r"[\s\-\(\)]", "", phone)


class DeleteAccountView(LoginRequiredMixin, View):
    def post(self, request):
        password = request.POST.get("password", "")
        
        if not request.user.check_password(password):
            messages.error(request, _("Incorrect password. Account deletion cancelled."))
            return redirect("core:settings")
        
        user = request.user
        
        logout(request)

        user.delete()
        
        messages.success(
            request, 
            _("Your account has been permanently deleted. We're sorry to see you go.")
        )
        return redirect("home")
