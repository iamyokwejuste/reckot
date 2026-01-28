import os

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings

from apps.core.models import OTPVerification
from apps.core.tasks import resend_otp_task


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
        from apps.events.models import Event
        featured_events = Event.objects.filter(
            is_featured=True,
            is_public=True,
            state=Event.State.PUBLISHED
        ).select_related('organization').order_by('feature_order', '-feature_approved_at')[:5]

        return render(request, 'core/home.html', {
            'featured_events': featured_events,
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
            user.phone = phone

        user.save()
        messages.success(request, 'Settings updated successfully.')
        return redirect('core:settings')
