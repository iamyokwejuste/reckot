import json
import logging

from django.views import View
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.payments.models import Payment, PaymentProvider, Invoice, Refund
from apps.payments.services import initiate_payment, confirm_payment, fail_payment
from apps.payments.queries import get_payment_by_id, get_booking_payment
from apps.payments.invoice_service import get_invoice_pdf, create_invoice
from apps.tickets.models import Booking
from apps.tickets.services import create_multi_ticket_booking
from apps.events.models import Event


class CheckoutView(LoginRequiredMixin, View):
    def post(self, request):
        event_id = request.POST.get('event_id')
        if not event_id:
            messages.error(request, 'Invalid event.')
            return redirect('events:discover')

        event = get_object_or_404(Event, id=event_id, state='PUBLISHED')

        ticket_selections = {}
        question_answers = {}

        for key, value in request.POST.items():
            if key.startswith('ticket_') and value:
                try:
                    ticket_type_id = int(key.replace('ticket_', ''))
                    quantity = int(value)
                    if quantity > 0:
                        ticket_selections[ticket_type_id] = quantity
                except (ValueError, TypeError):
                    continue
            elif key.startswith('question_') and value:
                try:
                    question_id = int(key.replace('question_', ''))
                    question_answers[question_id] = value
                except (ValueError, TypeError):
                    continue

        if not ticket_selections:
            messages.error(request, 'Please select at least one ticket.')
            return redirect('events:public_detail',
                          org_slug=event.organization.slug,
                          event_slug=event.slug)

        booking, error = create_multi_ticket_booking(
            user=request.user,
            event=event,
            ticket_selections=ticket_selections,
            question_answers=question_answers
        )

        if error:
            messages.error(request, error)
            return redirect('events:public_detail',
                          org_slug=event.organization.slug,
                          event_slug=event.slug)

        affiliate_code = request.POST.get('affiliate_code')
        if affiliate_code:
            request.session['affiliate_code'] = affiliate_code
            request.session['affiliate_booking'] = str(booking.reference)

        return redirect('payments:select', booking_ref=booking.reference)


class PaymentListView(LoginRequiredMixin, View):
    def get(self, request):
        payments = Payment.objects.filter(
            booking__event__organization__members=request.user
        ).select_related(
            'booking__user',
            'booking__event'
        ).order_by('-created_at')[:100]

        confirmed_payments = Payment.objects.filter(
            booking__event__organization__members=request.user,
            status=Payment.Status.CONFIRMED
        )

        stats = {
            'total_revenue': confirmed_payments.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'confirmed': confirmed_payments.count(),
            'pending': Payment.objects.filter(
                booking__event__organization__members=request.user,
                status=Payment.Status.PENDING
            ).count(),
        }

        return render(request, 'payments/list.html', {
            'payments': payments,
            'stats': stats,
        })


class PaymentSelectMethodView(LoginRequiredMixin, View):
    def get(self, request, booking_ref):
        booking = get_object_or_404(Booking, reference=booking_ref, user=request.user)
        existing_payment = get_booking_payment(booking.id)
        if existing_payment and existing_payment.status == Payment.Status.CONFIRMED:
            return redirect('payments:success', payment_ref=existing_payment.reference)
        return render(request, 'payments/select_method.html', {
            'booking': booking,
            'existing_payment': existing_payment,
            'methods': PaymentProvider.choices,
        })


class PaymentStartView(LoginRequiredMixin, View):
    def post(self, request, booking_ref):
        booking = get_object_or_404(Booking, reference=booking_ref, user=request.user)
        method = request.POST.get('method')
        phone = request.POST.get('phone')
        if not method or not phone:
            return render(request, 'payments/_error.html', {
                'error': 'Please select a payment method and enter your phone number'
            })
        payment, result = initiate_payment(booking, method, phone)
        if not result.get('success'):
            return render(request, 'payments/_error.html', {
                'error': result.get('message', 'Payment initiation failed')
            })
        response = render(request, 'payments/_pending.html', {'payment': payment})
        response['HX-Trigger'] = 'payment-started'
        return response


class PaymentPollView(LoginRequiredMixin, View):
    def get(self, request, payment_ref):
        payment = get_object_or_404(Payment, reference=payment_ref, booking__user=request.user)
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
    def get(self, request, payment_ref):
        payment = get_object_or_404(Payment, reference=payment_ref, booking__user=request.user)
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


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class CampayWebhookView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST.dict()

        logger.info(f'CamPay webhook received: {data}')

        external_reference = data.get('external_reference', '')
        campay_reference = data.get('reference', '')
        status = data.get('status', '').upper()

        if not external_reference:
            logger.warning('CamPay webhook missing external_reference')
            return HttpResponse('Missing reference', status=400)

        payment = get_payment_by_id(external_reference)
        if not payment:
            logger.warning(f'Payment not found for reference: {external_reference}')
            return HttpResponse('Payment not found', status=404)

        if status == 'SUCCESSFUL':
            confirm_payment(payment, campay_reference)
            logger.info(f'Payment {external_reference} confirmed via CamPay webhook')
        elif status == 'FAILED':
            fail_payment(payment, data.get('reason', 'Payment failed'))
            logger.info(f'Payment {external_reference} failed via CamPay webhook')

        return HttpResponse('OK', status=200)


class InvoiceDownloadView(LoginRequiredMixin, View):
    def get(self, request, payment_ref):
        payment = get_object_or_404(Payment, reference=payment_ref, booking__user=request.user)
        if payment.status != Payment.Status.CONFIRMED:
            messages.error(request, 'Invoice not available for unpaid orders.')
            return redirect('payments:list')

        try:
            invoice = payment.invoice
        except Invoice.DoesNotExist:
            invoice = create_invoice(payment)

        pdf_content = get_invoice_pdf(invoice)
        if not pdf_content:
            messages.error(request, 'Failed to generate invoice.')
            return redirect('payments:list')

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{invoice.invoice_number}.pdf"'
        return response


class RefundListView(LoginRequiredMixin, View):
    def get(self, request):
        refunds = Refund.objects.filter(
            payment__booking__event__organization__members=request.user
        ).select_related(
            'payment__booking__user',
            'payment__booking__event'
        ).order_by('-created_at')[:100]

        stats = {
            'pending': refunds.filter(status=Refund.Status.PENDING).count(),
            'approved': refunds.filter(status=Refund.Status.APPROVED).count(),
            'processed': refunds.filter(status=Refund.Status.PROCESSED).count(),
        }

        return render(request, 'payments/refunds/list.html', {
            'refunds': refunds,
            'stats': stats,
        })


class RefundRequestView(LoginRequiredMixin, View):
    def get(self, request, payment_ref):
        payment = get_object_or_404(
            Payment,
            reference=payment_ref,
            booking__user=request.user,
            status=Payment.Status.CONFIRMED
        )
        return render(request, 'payments/refunds/request.html', {'payment': payment})

    def post(self, request, payment_ref):
        payment = get_object_or_404(
            Payment,
            reference=payment_ref,
            booking__user=request.user,
            status=Payment.Status.CONFIRMED
        )

        existing_refund = Refund.objects.filter(
            payment=payment,
            status__in=[Refund.Status.PENDING, Refund.Status.APPROVED]
        ).exists()

        if existing_refund:
            messages.warning(request, 'A refund request already exists for this payment.')
            return redirect('payments:success', payment_ref=payment_ref)

        refund_type = request.POST.get('refund_type', 'FULL')
        amount = payment.amount if refund_type == 'FULL' else request.POST.get('amount', 0)
        reason = request.POST.get('reason', '').strip()

        Refund.objects.create(
            payment=payment,
            amount=amount,
            refund_type=refund_type,
            reason=reason,
            requested_by=request.user,
        )

        messages.success(request, 'Refund request submitted successfully.')
        return redirect('payments:success', payment_ref=payment_ref)


class RefundProcessView(LoginRequiredMixin, View):
    def get(self, request, refund_id):
        refund = get_object_or_404(
            Refund.objects.select_related('payment__booking__event__organization'),
            id=refund_id,
            payment__booking__event__organization__members=request.user
        )
        return render(request, 'payments/refunds/process.html', {'refund': refund})

    def post(self, request, refund_id):
        refund = get_object_or_404(
            Refund.objects.select_related('payment__booking__event__organization'),
            id=refund_id,
            payment__booking__event__organization__members=request.user
        )

        action = request.POST.get('action')

        if action == 'approve':
            refund.approve(processed_by=request.user)
            messages.success(request, 'Refund approved.')
        elif action == 'process':
            refund.process(processed_by=request.user)
            messages.success(request, 'Refund marked as processed.')
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            refund.reject(reason, processed_by=request.user)
            messages.success(request, 'Refund rejected.')

        return redirect('payments:refunds')
