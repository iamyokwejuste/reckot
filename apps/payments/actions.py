import hashlib
import hmac
import json
import logging
import re
from datetime import timedelta
from decimal import Decimal

import jwt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt

from apps.events.models import Coupon, Event
from apps.orgs.models import Organization
from apps.payments.gateways.campay import CampayGateway
from apps.payments.invoice_service import create_invoice, get_invoice_pdf
from apps.payments.models import Invoice, Payment, PaymentProvider, Refund, Withdrawal
from apps.payments.queries import get_booking_payment, get_payment_by_id
from apps.payments.services import (
    calculate_organization_balance,
    confirm_payment,
    fail_payment,
    initiate_payment,
    verify_and_confirm_payment,
)
from apps.tickets.models import Booking, GuestSession
from apps.tickets.services import create_multi_ticket_booking
from apps.tickets.tasks import send_ticket_confirmation_task


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

        attendee_info = {}
        for key in request.POST:
            if key.startswith("attendee_name_") or key.startswith("attendee_email_"):
                attendee_info[key] = request.POST.get(key, "").strip()

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
            attendee_info=attendee_info,
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

        if booking.total_amount == Decimal("0.00"):
            send_ticket_confirmation_task.delay(booking.id)
            messages.success(
                request,
                _(
                    "Your free tickets have been confirmed! Check your email for details."
                ),
            )
            return redirect("tickets:my_tickets")

        return redirect("payments:select", booking_ref=booking.reference)


class PaymentListView(LoginRequiredMixin, View):
    def get(self, request):
        status_filter = request.GET.get("status", "")
        page_number = request.GET.get("page", 1)

        payments_qs = Payment.objects.filter(
            booking__event__organization__members=request.user
        ).select_related("booking__user", "booking__event")

        if status_filter:
            payments_qs = payments_qs.filter(status=status_filter)

        payments_qs = payments_qs.order_by("-created_at")

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

        paginator = Paginator(payments_qs, 50)
        page_obj = paginator.get_page(page_number)

        return render(
            request,
            "payments/list.html",
            {
                "payments": page_obj.object_list,
                "page_obj": page_obj,
                "paginator": paginator,
                "status_filter": status_filter,
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


@method_decorator(csrf_exempt, name="dispatch")
class PaymentWebhookView(View):
    def _verify_hmac_signature(self, request, payment) -> bool:
        signature = request.headers.get("X-Webhook-Signature", "")
        if not signature:
            logger.error("Generic webhook missing signature header")
            return False

        gateway_config = payment.gateway_config
        if not gateway_config:
            logger.error("Payment has no gateway config")
            return False

        credentials = gateway_config.credentials or {}
        webhook_secret = credentials.get("webhook_secret", "")

        if not webhook_secret:
            logger.error("Webhook secret not configured")
            return False

        body = request.body.decode("utf-8")
        expected_signature = hmac.new(
            webhook_secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            logger.error("Webhook signature mismatch")
            return False

        logger.info("Generic webhook signature verified")
        return True

    def post(self, request):
        reference = request.POST.get("reference")
        status = request.POST.get("status")
        external_ref = request.POST.get("external_reference", "")
        payment = get_payment_by_id(reference)
        if not payment:
            return HttpResponse(status=404)

        if not self._verify_hmac_signature(request, payment):
            return HttpResponse("Invalid signature", status=403)

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
            logger.error("CamPay webhook missing signature - rejecting")
            return False

        gateway_config = payment.gateway_config
        if not gateway_config:
            logger.error("Payment has no gateway config - rejecting webhook")
            return False

        credentials = gateway_config.credentials or {}
        webhook_key = credentials.get("webhook_key", "")

        if not webhook_key:
            logger.error("Webhook key not configured - rejecting webhook")
            return False

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
    REFUND_WINDOW_DAYS = 30

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

        payment_age = timezone.now() - payment.created_at
        if payment_age > timedelta(days=self.REFUND_WINDOW_DAYS):
            messages.error(
                request,
                _(
                    f"Refund requests must be made within {self.REFUND_WINDOW_DAYS} days of payment."
                ),
            )
            return redirect("payments:success", payment_ref=payment_ref)

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
            payment.amount
            if refund_type == "FULL"
            else Decimal(request.POST.get("amount", "0"))
        )
        reason = request.POST.get("reason", "").strip()

        if refund_type == "PARTIAL" and amount > payment.amount:
            messages.error(
                request,
                _("Refund amount cannot exceed the original payment amount."),
            )
            return redirect("payments:success", payment_ref=payment_ref)

        if refund_type == "PARTIAL" and amount <= 0:
            messages.error(request, _("Refund amount must be greater than zero."))
            return redirect("payments:success", payment_ref=payment_ref)

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


class WithdrawalBalanceView(LoginRequiredMixin, View):
    @method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True))
    def get(self, request):
        user_org = Organization.objects.filter(members=request.user).first()

        if not user_org:
            return JsonResponse({"error": "No organization found"}, status=404)

        balance_data = calculate_organization_balance(user_org)

        return JsonResponse(
            {
                "available_balance": float(balance_data["available_balance"]),
                "total_revenue": float(balance_data["total_revenue"]),
                "total_service_fees": float(balance_data["service_fees"]),
                "total_withdrawn": float(balance_data["total_withdrawn"]),
                "total_refunded": float(balance_data["total_refunded"]),
                "currency": "XAF",
            }
        )


class WithdrawalRequestView(LoginRequiredMixin, View):
    MINIMUM_WITHDRAWAL_AMOUNT = Decimal("200")
    MAX_WITHDRAWALS_PER_DAY = 5
    PHONE_NUMBER_PATTERN = re.compile(r"^(\+?237)?[26][0-9]{8}$")

    def post(self, request):
        try:
            amount = Decimal(request.POST.get("amount", "0"))
            phone_number = request.POST.get("phone_number", "").strip()

            user_orgs = Organization.objects.filter(members=request.user).first()
            if not user_orgs:
                return JsonResponse(
                    {"success": False, "error": "No organization found"}, status=400
                )

            description = f"{user_orgs.name[:20]}"

            if amount < self.MINIMUM_WITHDRAWAL_AMOUNT:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Minimum withdrawal amount is {self.MINIMUM_WITHDRAWAL_AMOUNT} XAF",
                    },
                    status=400,
                )

            if not phone_number:
                return JsonResponse(
                    {"success": False, "error": "Phone number is required"}, status=400
                )

            if not self.PHONE_NUMBER_PATTERN.match(phone_number):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Invalid phone number format. Expected Cameroon number (e.g., +237XXXXXXXXX)",
                    },
                    status=400,
                )

            today_start = timezone.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            todays_withdrawals = Withdrawal.objects.filter(
                organization=user_orgs, created_at__gte=today_start
            ).count()

            if todays_withdrawals >= self.MAX_WITHDRAWALS_PER_DAY:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Maximum {self.MAX_WITHDRAWALS_PER_DAY} withdrawals per day exceeded. Try again tomorrow.",
                    },
                    status=429,
                )

            balance_data = calculate_organization_balance(user_orgs)
            available_balance = balance_data["available_balance"]

            if available_balance < self.MINIMUM_WITHDRAWAL_AMOUNT:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Minimum balance required is {self.MINIMUM_WITHDRAWAL_AMOUNT} XAF. Your balance: {available_balance} XAF",
                    },
                    status=400,
                )

            if amount > available_balance:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Insufficient balance. Available: {available_balance} XAF",
                    },
                    status=400,
                )

            gateway_credentials = {
                "app_username": settings.CAMPAY_USERNAME,
                "app_password": settings.CAMPAY_PASSWORD,
                "permanent_token": getattr(settings, "CAMPAY_TOKEN", ""),
                "is_production": getattr(settings, "CAMPAY_PRODUCTION", False),
            }

            gateway = CampayGateway(gateway_credentials)
            gateway_fee = Decimal("0")

            platform_commission_percent = Decimal("7")
            platform_commission = (
                amount * platform_commission_percent / Decimal("100")
            ).quantize(Decimal("1"))

            net_amount = amount - platform_commission

            withdrawal = Withdrawal.objects.create(
                organization=user_orgs,
                amount=amount,
                gateway_fee=gateway_fee,
                platform_commission=platform_commission,
                net_amount=net_amount,
                phone_number=phone_number,
                description=description,
                requested_by=request.user,
            )

            withdrawal.mark_processing()

            result = gateway.disburse(
                amount=net_amount,
                currency="XAF",
                phone_number=phone_number,
                description=description,
                external_reference=str(withdrawal.external_reference),
                wait_for_completion=False,
            )

            if result.success:
                withdrawal.gateway_response = result.raw_response or {}
                withdrawal.save(update_fields=["gateway_response", "updated_at"])

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Withdrawal request submitted successfully",
                        "reference": str(withdrawal.reference),
                        "net_amount": float(net_amount),
                        "platform_commission": float(platform_commission),
                    }
                )
            else:
                withdrawal.mark_failed(result.message)
                return JsonResponse(
                    {"success": False, "error": result.message}, status=400
                )

        except Exception as e:
            logger.error(f"Withdrawal request failed: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class WithdrawalListView(LoginRequiredMixin, View):
    def get(self, request):
        user_orgs = Organization.objects.filter(members=request.user)

        withdrawals = Withdrawal.objects.filter(
            organization__in=user_orgs
        ).select_related("organization", "requested_by")

        status_filter = request.GET.get("status")
        if status_filter:
            withdrawals = withdrawals.filter(status=status_filter)

        stats = {
            "pending": withdrawals.filter(status=Withdrawal.Status.PENDING).count(),
            "processing": withdrawals.filter(
                status=Withdrawal.Status.PROCESSING
            ).count(),
            "completed": withdrawals.filter(status=Withdrawal.Status.COMPLETED).count(),
            "failed": withdrawals.filter(status=Withdrawal.Status.FAILED).count(),
        }

        return render(
            request,
            "payments/withdrawals/list.html",
            {
                "withdrawals": withdrawals[:50],
                "stats": stats,
                "status_filter": status_filter,
            },
        )


class TransactionHistoryView(LoginRequiredMixin, View):
    @method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True))
    def get(self, request):
        user_org = Organization.objects.filter(members=request.user).first()

        if not user_org:
            return render(
                request, "payments/transactions/history.html", {"transactions": []}
            )

        transactions = []

        payments = Payment.objects.filter(
            booking__event__organization=user_org, status=Payment.Status.CONFIRMED
        ).select_related("booking__event", "booking__user")

        for payment in payments:
            transactions.append(
                {
                    "date": payment.confirmed_at or payment.created_at,
                    "type": "credit",
                    "description": f"Payment for {payment.booking.event.title}",
                    "amount": payment.amount,
                    "balance_change": f"+{payment.amount - payment.service_fee}",
                    "reference": str(payment.reference),
                }
            )

        withdrawals = Withdrawal.objects.filter(
            organization=user_org,
            status__in=[Withdrawal.Status.COMPLETED, Withdrawal.Status.PROCESSING],
        ).select_related("organization")

        for withdrawal in withdrawals:
            transactions.append(
                {
                    "date": withdrawal.created_at,
                    "type": "debit",
                    "description": f"Withdrawal to {withdrawal.phone_number}",
                    "amount": withdrawal.amount,
                    "balance_change": f"-{withdrawal.amount}",
                    "reference": str(withdrawal.reference),
                }
            )

        refunds = Refund.objects.filter(
            payment__booking__event__organization=user_org,
            status=Refund.Status.PROCESSED,
        ).select_related("payment__booking__event")

        for refund in refunds:
            transactions.append(
                {
                    "date": refund.processed_at or refund.created_at,
                    "type": "debit",
                    "description": f"Refund for {refund.payment.booking.event.title}",
                    "amount": refund.amount,
                    "balance_change": f"-{refund.amount}",
                    "reference": str(refund.reference),
                }
            )

        transactions.sort(key=lambda x: x["date"], reverse=True)

        balance_data = calculate_organization_balance(user_org)

        return render(
            request,
            "payments/transactions/history.html",
            {
                "transactions": transactions[:100],
                "balance_data": balance_data,
            },
        )
