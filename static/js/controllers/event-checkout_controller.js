import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = [
        "couponInput",
        "couponError", "couponErrorContainer",
        "couponDiscount", "couponDiscountContainer",
        "deliveryError", "deliveryErrorContainer"
    ]

    static values = {
        csrfToken: String,
        eventId: String,
        validateCouponUrl: String
    }

    connect() {
        this.couponValid = null;
        this.deliveryMethod = 'EMAIL_ALL';
    }

    disconnect() {
    }

    async validateCoupon() {
        const code = this.couponInputTarget.value.trim();

        if (!code) {
            this.resetCouponState();
            return;
        }

        try {
            const response = await fetch(this.validateCouponUrlValue, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.csrfTokenValue
                },
                body: `code=${encodeURIComponent(code)}&event_id=${this.eventIdValue}`
            });

            const data = await response.json();
            this.couponValid = data.valid;

            if (data.valid) {
                this.showCouponSuccess(data);
            } else {
                this.showCouponError(data.error);
            }
        } catch (e) {
            this.showCouponError('Failed to validate coupon');
        }
    }

    validateDeliveryEmails(event) {
        if (this.deliveryMethod !== 'EMAIL_INDIVIDUALLY') {
            return true;
        }

        const form = event.target;
        const emailInputs = form.querySelectorAll('input[name^="attendee_email_"]');
        const emails = [];
        const emptyEmails = [];

        emailInputs.forEach(input => {
            const email = input.value.trim();
            if (email) {
                emails.push(email.toLowerCase());
            } else {
                emptyEmails.push(input);
            }
        });

        if (emptyEmails.length > 0) {
            this.showDeliveryError('Please fill in email addresses for all attendees when using individual delivery.');
            event.preventDefault();
            emptyEmails[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
            emptyEmails[0].focus();
            return false;
        }

        const uniqueEmails = new Set(emails);
        if (uniqueEmails.size !== emails.length) {
            this.showDeliveryError('Each attendee must have a unique email address for individual delivery.');
            event.preventDefault();
            return false;
        }

        this.clearDeliveryError();
        return true;
    }

    updateDeliveryMethod(event) {
        this.deliveryMethod = event.target.value;
        this.clearDeliveryError();
    }

    resetCouponState() {
        this.couponValid = null;

        if (this.hasCouponErrorContainerTarget) {
            this.couponErrorContainerTarget.classList.add('hidden');
        }

        if (this.hasCouponDiscountContainerTarget) {
            this.couponDiscountContainerTarget.classList.add('hidden');
        }
    }

    showCouponSuccess(data) {
        if (this.hasCouponErrorContainerTarget) {
            this.couponErrorContainerTarget.classList.add('hidden');
        }

        if (this.hasCouponDiscountTarget && this.hasCouponDiscountContainerTarget) {
            const discount = data.discount_type === 'PERCENTAGE'
                ? `${data.discount_value}% off`
                : `${data.discount_value} XAF off`;

            this.couponDiscountTarget.textContent = discount;
            this.couponDiscountContainerTarget.classList.remove('hidden');
        }
    }

    showCouponError(message) {
        this.couponValid = false;

        if (this.hasCouponDiscountContainerTarget) {
            this.couponDiscountContainerTarget.classList.add('hidden');
        }

        if (this.hasCouponErrorTarget && this.hasCouponErrorContainerTarget) {
            this.couponErrorTarget.textContent = message;
            this.couponErrorContainerTarget.classList.remove('hidden');
        }
    }

    showDeliveryError(message) {
        if (this.hasDeliveryErrorTarget && this.hasDeliveryErrorContainerTarget) {
            this.deliveryErrorTarget.textContent = message;
            this.deliveryErrorContainerTarget.classList.remove('hidden');
        }
    }

    clearDeliveryError() {
        if (this.hasDeliveryErrorContainerTarget) {
            this.deliveryErrorContainerTarget.classList.add('hidden');
        }
    }
}
