import os
import re

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings

from apps.core.models import OTPVerification, User
from apps.core.tasks import resend_otp_task
from apps.core.services.notifications import NotificationService
from apps.events.models import Event


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


def service_worker(request):
    sw_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'sw.js')
    if not os.path.exists(sw_path):
        sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    try:
        with open(sw_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse('', content_type='application/javascript', status=404)


class HomeView(View):
    def get(self, request):
        featured_events = Event.objects.filter(
            is_featured=True,
            is_public=True,
            state=Event.State.PUBLISHED
        ).select_related('organization').order_by('feature_order', '-feature_approved_at')[:5]

        user_has_events = False
        if request.user.is_authenticated:
            user_has_events = Event.objects.filter(
                organization__members=request.user
            ).exists()

        return render(request, 'core/home.html', {
            'featured_events': featured_events,
            'user_has_events': user_has_events,
        })


class WhyUsView(View):
    def get(self, request):
        return render(request, 'core/why_us.html')


class PrivacyView(View):
    def get(self, request):
        return render(request, 'core/privacy.html')


class TermsView(View):
    def get(self, request):
        return render(request, 'core/terms.html')


class FeaturesView(View):
    def get(self, request):
        return render(request, 'core/features.html')


class OTPVerificationView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.email_verified:
            return redirect('home')
        return render(request, 'account/otp_verify.html')

    def post(self, request):
        if request.user.email_verified:
            return redirect('home')

        code = request.POST.get('otp_code', '').strip()
        if not code or len(code) != 6:
            messages.error(request, 'Please enter a valid 6-digit code.')
            return render(request, 'account/otp_verify.html')

        otp = OTPVerification.objects.filter(
            user=request.user,
            otp_type=OTPVerification.Type.EMAIL,
            is_used=False
        ).order_by('-created_at').first()

        if not otp:
            messages.error(request, 'No verification code found. Please request a new one.')
            return render(request, 'account/otp_verify.html')

        if otp.verify(code):
            request.user.email_verified = True
            request.user.save(update_fields=['email_verified'])
            messages.success(request, 'Email verified successfully!')
            return redirect('home')
        elif otp.is_expired:
            messages.error(request, 'Code expired. Please request a new one.')
        elif otp.attempts >= 5:
            messages.error(request, 'Too many attempts. Please request a new code.')
        else:
            messages.error(request, 'Invalid code. Please try again.')

        return render(request, 'account/otp_verify.html')


class ResendOTPView(LoginRequiredMixin, View):
    def post(self, request):
        if request.user.email_verified:
            return JsonResponse({'success': False, 'message': 'Email already verified'})

        resend_otp_task(request.user.id, OTPVerification.Type.EMAIL)
        return JsonResponse({'success': True, 'message': 'New code sent to your email'})


class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'core/settings.html', {
            'user': request.user,
        })

    def post(self, request):
        user = request.user
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if phone:
            user.phone_number = re.sub(r'[\s\-\(\)]', '', phone)

        user.save()
        messages.success(request, 'Settings updated successfully.')
        return redirect('core:settings')


class PhoneLoginRequestView(View):
    def get(self, request):
        return redirect('account_login')

    def post(self, request):
        phone = request.POST.get('phone_number', '').strip()
        if not phone:
            return HttpResponse(
                '<p class="text-sm text-red-500 mt-2">Please enter a phone number</p>',
                status=400
            )

        phone = self._normalize_phone(phone)
        user = User.objects.filter(phone_number=phone).first()
        if not user:
            return HttpResponse(
                '<p class="text-sm text-red-500 mt-2">No account found with this phone number</p>',
                status=400
            )

        otp = OTPVerification.create_for_user(user, OTPVerification.Type.PHONE)
        self._send_otp_sms(phone, otp.code)
        return HttpResponse(
            '<p class="text-sm text-emerald-500 mt-2">Verification code sent!</p>'
        )

    def _normalize_phone(self, phone):
        return re.sub(r'[\s\-\(\)]', '', phone)

    def _send_otp_sms(self, phone, code):
        NotificationService.send_otp_sms(phone, code)


class PhoneLoginVerifyView(View):
    def get(self, request):
        return redirect('account_login')

    def post(self, request):
        phone = request.POST.get('phone_number', '').strip()
        code = request.POST.get('otp_code', '').strip()

        if not phone or not code:
            messages.error(request, 'Phone number and code are required')
            return redirect('account_login')

        phone = self._normalize_phone(phone)
        user = User.objects.filter(phone_number=phone).first()
        if not user:
            messages.error(request, 'Invalid phone number')
            return redirect('account_login')

        otp = OTPVerification.objects.filter(
            user=user,
            otp_type=OTPVerification.Type.PHONE,
            is_used=False
        ).order_by('-created_at').first()

        if not otp:
            messages.error(request, 'No verification code found. Please request a new one.')
            return redirect('account_login')

        if otp.verify(code):
            user.phone_verified = True
            user.save(update_fields=['phone_verified'])
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Logged in successfully!')
            return redirect('home')
        elif otp.is_expired:
            messages.error(request, 'Code expired. Please request a new one.')
        elif otp.attempts >= 5:
            messages.error(request, 'Too many attempts. Please request a new code.')
        else:
            messages.error(request, 'Invalid code. Please try again.')

        return redirect('account_login')

    def _normalize_phone(self, phone):
        return re.sub(r'[\s\-\(\)]', '', phone)


class PhoneSignupRequestView(View):
    def get(self, request):
        return redirect('account_signup')

    def post(self, request):
        phone = request.POST.get('phone_number', '').strip()
        if not phone:
            return HttpResponse(
                '<p class="text-sm text-red-500 mt-2">Please enter a phone number</p>',
                status=400
            )

        phone = self._normalize_phone(phone)
        if User.objects.filter(phone_number=phone).exists():
            return HttpResponse(
                '<p class="text-sm text-red-500 mt-2">An account with this phone number already exists</p>',
                status=400
            )

        request.session['signup_phone'] = phone
        request.session['signup_otp'] = OTPVerification.generate_code()
        self._send_otp_sms(phone, request.session['signup_otp'])
        return HttpResponse(
            '<p class="text-sm text-emerald-500 mt-2">Verification code sent!</p>'
        )

    def _normalize_phone(self, phone):
        return re.sub(r'[\s\-\(\)]', '', phone)

    def _send_otp_sms(self, phone, code):
        NotificationService.send_otp_sms(phone, code)


class PhoneSignupVerifyView(View):
    def get(self, request):
        return redirect('account_signup')

    def post(self, request):
        phone = request.POST.get('phone_number', '').strip()
        code = request.POST.get('otp_code', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        phone = self._normalize_phone(phone)
        stored_phone = request.session.get('signup_phone')
        stored_otp = request.session.get('signup_otp')

        if phone != stored_phone:
            messages.error(request, 'Phone number mismatch. Please start over.')
            return redirect('account_signup')

        if code != stored_otp:
            messages.error(request, 'Invalid verification code')
            return redirect('account_signup')

        if not password1 or password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('account_signup')

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('account_signup')

        user = User.objects.create_user(
            username=phone,
            phone_number=phone,
            phone_verified=True,
            password=password1
        )

        del request.session['signup_phone']
        del request.session['signup_otp']

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Account created successfully!')
        return redirect('home')

    def _normalize_phone(self, phone):
        return re.sub(r'[\s\-\(\)]', '', phone)
