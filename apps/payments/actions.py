import json
import logging
from datetime import timedelta

import jwt
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.events.models import Coupon, Event
from apps.payments.invoice_service import create_invoice, get_invoice_pdf
from apps.payments.models import Invoice, Payment, PaymentProvider, Refund
from apps.payments.queries import get_booking_payment, get_payment_by_id
from apps.payments.services import (
    confirm_payment,
    fail_payment,
    initiate_payment,
    verify_and_confirm_payment,
)
from apps.tickets.models import Booking, GuestSession
from apps.tickets.services import create_multi_ticket_booking


class CheckoutView(View):
    def post(self, request):
        event_id = request.POST.get("event_id")
        if not event_id:
            messages.error(request, _("Invalid event."))
            return redirect("events:discover")

        event = get_object_or_404(Event, id=event_id, state="PUBLISHED")

        ticket_selections = {}
        question_answers = {}

        for key, value in request.POST.items():
            if key.startswith("ticket_") and value:
                try:
                    ticket_type_id = int(key.replace("ticket_", ""))
                    quantity = int(value)
                    if quantity > 0:
                        ticket_selections[ticket_type_id] = quantity
                except (ValueError, TypeError):
                    continue
            elif key.startswith("question_") and value:
                try:
                    question_id = int(key.replace("question_", ""))
                    question_answers[question_id] = value
                except (ValueError, TypeError):
                    continue

        if not ticket_selections:
            messages.error(request, _("Please select at least one ticket."))
            return redirect(
                "events:public_detail",
                org_slug=event.organization.slug,
                event_slug=event.slug,
            )

        coupon_code = request.POST.get("coupon_code", "").strip().upper()
        coupon = None
        user = request.user if request.user.is_authenticated else None
        guest_email = None

        if coupon_code:
            email_for_coupon = (
                request.user.email if user else request.POST.get("guest_email", "")
            )
            coupon = Coupon.objects.filter(
                Q(code=coupon_code),
                Q(event=event) | Q(event__isnull=True, organization=event.organization),
                is_active=True,
            ).first()
            if coupon and not coupon.is_valid:
                coupon = None
            if (
                coupon
                and email_for_coupon
                and not coupon.can_be_used_by(email_for_coupon)
            ):
                coupon = None

        guest_session = None
        guest_name = None
        guest_phone = None

        if not user:
            guest_email = request.POST.get("guest_email", "").strip()
            guest_name = request.POST.get("guest_name", "").strip()
            guest_phone = request.POST.get("guest_phone", "").strip()

            if not guest_email:
                messages.error(request, _("Please enter your email address."))
                return redirect(
                    "events:public_detail",
                    org_slug=event.organization.slug,
                    event_slug=event.slug,
                )

            if not guest_name:
                messages.error(request, _("Please enter your name."))
                return redirect(
                    "events:public_detail",
                    org_slug=event.organization.slug,
                    event_slug=event.slug,
                )

            guest_session = GuestSession.objects.create(
                email=guest_email,
                name=guest_name,
                phone=guest_phone,
                expires_at=timezone.now() + timedelta(hours=24),
            )
            request.session["guest_token"] = str(guest_session.token)

        booking, error = create_multi_ticket_booking(
            user=user,
            event=event,
            ticket_selections=ticket_selections,
            question_answers=question_answers,
            coupon=coupon,
            guest_session=guest_session,
            guest_email=guest_email,
            guest_name=guest_name,
            guest_phone=guest_phone,
        )

        if error:
            messages.error(request, error)
            return redirect(
                "events:public_detail",
                org_slug=event.organization.slug,
                event_slug=event.slug,
            )

        affiliate_code = request.POST.get("affiliate_code")
        if affiliate_code:
            request.session["affiliate_code"] = affiliate_code
            request.session["affiliate_booking"] = str(booking.reference)

        return redirect("payments:select", booking_ref=booking.reference)


class PaymentListView(LoginRequiredMixin, View):
    def get(self, request):
        payments = (
            Payment.objects.filter(booking__event__organization__members=request.user)
            .select_related("booking__user", "booking__event")
            .order_by("-created_at")[:100]
        )

        confirmed_payments = Payment.objects.filter(
            booking__event__organization__members=request.user,
            status=Payment.Status.CONFIRMED,
        )

        stats = {
            "total_revenue": confirmed_payments.aggregate(total=Sum("amount"))["total"]
            or 0,
            "confirmed": confirmed_payments.count(),
            "pending": Payment.objects.filter(
                booking__event__organization__members=request.user,
                status=Payment.Status.PENDING,
            ).count(),
        }

        return render(
            request,
            "payments/list.html",
            {
                "payments": payments,
                "stats": stats,
            },
        )


def get_booking_for_request(request, booking_ref):
    if request.user.is_authenticated:
        booking = Booking.objects.filter(
            reference=booking_ref, user=request.user
        ).first()
        if booking:
            return booking, None

    guest_token = request.session.get("guest_token")
    if guest_token:
        booking = Booking.objects.filter(
            reference=booking_ref, guest_session__token=guest_token
        ).first()
        if booking:
            return booking, None

    return None, redirect("events:discover")


class PaymentSelectMethodView(View):
    def _calculate_withdrawal_fee(self, amount):
        from decimal import Decimal

        if amount <= 1000:
            return Decimal("50")
        return (Decimal(str(amount)) * Decimal("0.04")).quantize(Decimal("1"))

    def get(self, request, booking_ref):
        booking, error = get_booking_for_request(request, booking_ref)
        if error:
            messages.error(request, _("Booking not found."))
            return error
        existing_payment = get_booking_payment(booking.id)
        if existing_payment and existing_payment.status == Payment.Status.CONFIRMED:
            return redirect("payments:success", payment_ref=existing_payment.reference)

        subtotal = booking.total_amount
        withdrawal_fee = self._calculate_withdrawal_fee(subtotal)
        total_with_fee = subtotal + withdrawal_fee

        return render(
            request,
            "payments/select_method.html",
            {
                "booking": booking,
                "existing_payment": existing_payment,
                "methods": PaymentProvider.choices,
                "subtotal": subtotal,
                "withdrawal_fee": withdrawal_fee,
                "total_with_fee": total_with_fee,
            },
        )


class PaymentStartView(View):
    def post(self, request, booking_ref):
        booking, error = get_booking_for_request(request, booking_ref)
        if error:
            return render(
                request, "payments/_error.html", {"error": _("Booking not found.")}
            )
        method = request.POST.get("method")
        phone = request.POST.get("phone")
        if not method or not phone:
            return render(
                request,
                "payments/_error.html",
                {
                    "error": _(
                        "Please select a payment method and enter your phone number"
                    )
                },
            )
        payment, result = initiate_payment(booking, method, phone)
        if not result.get("success"):
            return render(
                request,
                "payments/_error.html",
                {"error": result.get("message", _("Payment initiation failed"))},
            )
        response = render(request, "payments/_pending.html", {"payment": payment})
        response["HX-Trigger"] = "payment-started"
        return response


def get_payment_for_request(request, payment_ref):
    if request.user.is_authenticated:
        payment = Payment.objects.filter(
            reference=payment_ref, booking__user=request.user
        ).first()
        if payment:
            return payment, None

    guest_token = request.session.get("guest_token")
    if guest_token:
        payment = Payment.objects.filter(
            reference=payment_ref, booking__guest_session__token=guest_token
        ).first()
        if payment:
            return payment, None

    return None, True


class PaymentPollView(View):
    def get(self, request, payment_ref):
        payment, error = get_payment_for_request(request, payment_ref)
        if error:
            return render(
                request, "payments/_error.html", {"error": _("Payment not found.")}
            )
        if payment.status == Payment.Status.CONFIRMED:
            return render(request, "payments/_success.html", {"payment": payment})
        if payment.status in [Payment.Status.FAILED, Payment.Status.EXPIRED]:
            return render(request, "payments/_failed.html", {"payment": payment})
        if payment.is_expired:
            payment.status = Payment.Status.EXPIRED
            payment.save()
            return render(request, "payments/_failed.html", {"payment": payment})

        if payment.status == Payment.Status.PENDING and payment.external_reference:
            verify_and_confirm_payment(payment)
            payment.refresh_from_db()
            if payment.status == Payment.Status.CONFIRMED:
                return render(request, "payments/_success.html", {"payment": payment})
            if payment.status == Payment.Status.FAILED:
                return render(request, "payments/_failed.html", {"payment": payment})

        return render(request, "payments/_pending.html", {"payment": payment})


class PaymentSuccessView(View):
    def get(self, request, payment_ref):
        payment, error = get_payment_for_request(request, payment_ref)
        if error:
            messages.error(request, _("Payment not found."))
            return redirect("events:discover")
        return render(request, "payments/success.html", {"payment": payment})


class PaymentWebhookView(View):
    def post(self, request):
        reference = request.POST.get("reference")
        status = request.POST.get("status")
        external_ref = request.POST.get("external_reference", "")
        payment = get_payment_by_id(reference)
        if not payment:
            return HttpResponse(status=404)
        if status == "SUCCESS":
            confirm_payment(payment, external_ref)
        return HttpResponse(status=200)


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class CampayWebhookView(View):
    def _get_webhook_data(self, request):
        if request.method == "GET":
            return request.GET.dict()
        try:
            return json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return request.POST.dict()

    def _verify_signature(self, signature: str, payment) -> bool:
        if not signature:
            logger.warning("CamPay webhook missing signature")
            return True

        gateway_config = payment.gateway_config
        if not gateway_config:
            return True

        credentials = gateway_config.credentials or {}
        webhook_key = credentials.get("webhook_key", "")

        if not webhook_key:
            return True

        try:
            jwt.decode(signature, webhook_key, algorithms=["HS256"])
            logger.info("CamPay webhook signature verified")
            return True
        except jwt.ExpiredSignatureError:
            logger.error("CamPay webhook signature expired")
            return False
        except jwt.InvalidTokenError as e:
            logger.error(f"CamPay webhook signature invalid: {e}")
            return False

    def _process_webhook(self, request):
        data = self._get_webhook_data(request)
        logger.info(f"CamPay webhook received ({request.method}): {data}")

        external_reference = data.get("external_reference", "")
        campay_reference = data.get("reference", "")
        status = data.get("status", "").upper()
        signature = data.get("signature", "")
        operator = data.get("operator", "")
        amount = data.get("amount", "")
        currency = data.get("currency", "")
        phone_number = data.get("phone_number", "")

        if not external_reference:
            logger.warning("CamPay webhook missing external_reference")
            return HttpResponse("Missing external_reference", status=400)

        payment = get_payment_by_id(external_reference)
        if not payment:
            logger.warning(f"Payment not found for reference: {external_reference}")
            return HttpResponse("Payment not found", status=404)

        if not self._verify_signature(signature, payment):
            logger.error(
                f"CamPay webhook signature verification failed for {external_reference}"
            )
            return HttpResponse("Invalid signature", status=403)

        webhook_data = {
            "campay_reference": campay_reference,
            "operator": operator,
            "amount": amount,
            "currency": currency,
            "phone_number": phone_number,
            "webhook_received_at": timezone.now().isoformat(),
        }

        if payment.metadata:
            payment.metadata.update(webhook_data)
        else:
            payment.metadata = webhook_data
        payment.save(update_fields=["metadata"])

        if status == "SUCCESSFUL":
            confirm_payment(payment, campay_reference)
            logger.info(f"Payment {external_reference} confirmed via CamPay webhook")
        elif status == "FAILED":
            reason = data.get("reason", "") or "Payment failed"
            fail_payment(payment, reason)
            logger.info(
                f"Payment {external_reference} failed via CamPay webhook: {reason}"
            )

        return HttpResponse("OK", status=200)

    def get(self, request):
        return self._process_webhook(request)

    def post(self, request):
        return self._process_webhook(request)


class InvoiceDownloadView(View):
    def get(self, request, payment_ref):
        payment, error = get_payment_for_request(request, payment_ref)
        if error:
            messages.error(request, _("Payment not found."))
            return redirect("events:discover")
        if payment.status != Payment.Status.CONFIRMED:
            messages.error(request, _("Invoice not available for unpaid orders."))
            return redirect("events:discover")

        try:
            invoice = payment.invoice
        except Invoice.DoesNotExist:
            invoice = create_invoice(payment)

        pdf_content = get_invoice_pdf(invoice)
        if not pdf_content:
            messages.error(request, _("Failed to generate invoice."))
            return redirect("events:discover")

        response = HttpResponse(pdf_content, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="{invoice.invoice_number}.pdf"'
        )
        return response


class RefundListView(LoginRequiredMixin, View):
    def get(self, request):
        base_refunds = Refund.objects.filter(
            payment__booking__event__organization__members=request.user
        )

        stats = {
            "pending": base_refunds.filter(status=Refund.Status.PENDING).count(),
            "approved": base_refunds.filter(status=Refund.Status.APPROVED).count(),
            "processed": base_refunds.filter(status=Refund.Status.PROCESSED).count(),
        }

        refunds = base_refunds.select_related(
            "payment__booking__user", "payment__booking__event"
        ).order_by("-created_at")[:100]

        return render(
            request,
            "payments/refunds/list.html",
            {
                "refunds": refunds,
                "stats": stats,
            },
        )


class RefundRequestView(LoginRequiredMixin, View):
    def get(self, request, payment_ref):
        payment = get_object_or_404(
            Payment,
            reference=payment_ref,
            booking__user=request.user,
            status=Payment.Status.CONFIRMED,
        )
        return render(request, "payments/refunds/request.html", {"payment": payment})

    def post(self, request, payment_ref):
        payment = get_object_or_404(
            Payment,
            reference=payment_ref,
            booking__user=request.user,
            status=Payment.Status.CONFIRMED,
        )

        existing_refund = Refund.objects.filter(
            payment=payment, status__in=[Refund.Status.PENDING, Refund.Status.APPROVED]
        ).exists()

        if existing_refund:
            messages.warning(
                request, _("A refund request already exists for this payment.")
            )
            return redirect("payments:success", payment_ref=payment_ref)

        refund_type = request.POST.get("refund_type", "FULL")
        amount = (
            payment.amount if refund_type == "FULL" else request.POST.get("amount", 0)
        )
        reason = request.POST.get("reason", "").strip()

        Refund.objects.create(
            payment=payment,
            amount=amount,
            refund_type=refund_type,
            reason=reason,
            requested_by=request.user,
        )

        messages.success(request, _("Refund request submitted successfully."))
        return redirect("payments:success", payment_ref=payment_ref)


class RefundProcessView(LoginRequiredMixin, View):
    def get(self, request, refund_id):
        refund = get_object_or_404(
            Refund.objects.select_related("payment__booking__event__organization"),
            id=refund_id,
            payment__booking__event__organization__members=request.user,
        )
        return render(request, "payments/refunds/process.html", {"refund": refund})

    def post(self, request, refund_id):
        refund = get_object_or_404(
            Refund.objects.select_related("payment__booking__event__organization"),
            id=refund_id,
            payment__booking__event__organization__members=request.user,
        )

        action = request.POST.get("action")

        if action == "approve":
            refund.approve(processed_by=request.user)
            messages.success(request, _("Refund approved."))
        elif action == "process":
            refund.process(processed_by=request.user)
            messages.success(request, _("Refund marked as processed."))
        elif action == "reject":
            reason = request.POST.get("rejection_reason", "")
            refund.reject(reason, processed_by=request.user)
            messages.success(request, _("Refund rejected."))

        return redirect("payments:refunds")


class TransactionStatusView(View):
    def get(self, request, token):
        guest_session = get_object_or_404(GuestSession, token=token)
        bookings = (
            Booking.objects.filter(guest_session=guest_session)
            .select_related("event", "payment")
            .prefetch_related("tickets")
        )
        return render(
            request,
            "payments/transaction_status.html",
            {
                "guest_session": guest_session,
                "bookings": bookings,
            },
        )
