from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse

from .models import OTPVerification
from .tasks import resend_otp_task


class HomeView(View):
    def get(self, request):
        return render(request, 'core/home.html')


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
