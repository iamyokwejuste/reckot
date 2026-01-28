from django.views import View
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Payment
from .services import initiate_payment, confirm_payment
from .queries import get_payment_by_id, get_booking_payment
from apps.tickets.models import Booking


class PaymentSelectMethodView(LoginRequiredMixin, View):
    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        existing_payment = get_booking_payment(booking_id)
        if existing_payment and existing_payment.status == Payment.Status.CONFIRMED:
            return redirect('payments:success', payment_id=existing_payment.id)
        return render(request, 'payments/select_method.html', {
            'booking': booking,
            'existing_payment': existing_payment,
            'methods': Payment.Method.choices,
        })


class PaymentStartView(LoginRequiredMixin, View):
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        method = request.POST.get('method')
        phone = request.POST.get('phone')
        if not method or not phone:
            return render(request, 'payments/_error.html', {
                'error': 'Please select a payment method and enter your phone number'
            })
        payment = initiate_payment(booking, method, phone)
        response = render(request, 'payments/_pending.html', {'payment': payment})
        response['HX-Trigger'] = 'payment-started'
        return response


class PaymentPollView(LoginRequiredMixin, View):
    def get(self, request, payment_id):
        payment = get_object_or_404(Payment, pk=payment_id, booking__user=request.user)
        if payment.status == Payment.Status.CONFIRMED:
            return render(request, 'payments/_success.html', {'payment': payment})
        if payment.status in [Payment.Status.FAILED, Payment.Status.EXPIRED]:
            return render(request, 'payments/_failed.html', {'payment': payment})
        if payment.is_expired:
            payment.status = Payment.Status.EXPIRED
            payment.save()
            return render(request, 'payments/_failed.html', {'payment': payment})
        return render(request, 'payments/_pending.html', {'payment': payment})


class PaymentSuccessView(LoginRequiredMixin, View):
    def get(self, request, payment_id):
        payment = get_object_or_404(Payment, pk=payment_id, booking__user=request.user)
        return render(request, 'payments/success.html', {'payment': payment})


class PaymentWebhookView(View):
    def post(self, request):
        reference = request.POST.get('reference')
        status = request.POST.get('status')
        external_ref = request.POST.get('external_reference', '')
        payment = get_payment_by_id(reference)
        if not payment:
            return HttpResponse(status=404)
        if status == 'SUCCESS':
            confirm_payment(payment, external_ref)
        return HttpResponse(status=200)
