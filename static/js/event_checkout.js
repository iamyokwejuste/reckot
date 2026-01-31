document.addEventListener('alpine:init', () => {
    Alpine.data('eventCheckout', (csrfToken, eventId, validateCouponUrl) => ({
        couponCode: '',
        couponValid: null,
        couponError: '',
        couponDiscount: null,
        discountType: '',
        discountValue: 0,
        deliveryMethod: 'EMAIL_ALL',
        deliveryError: '',

        async validateCoupon() {
            if (!this.couponCode.trim()) {
                this.couponValid = null;
                this.couponError = '';
                this.couponDiscount = null;
                return;
            }
            try {
                const response = await fetch(validateCouponUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken
                    },
                    body: `code=${encodeURIComponent(this.couponCode)}&event_id=${eventId}`
                });
                const data = await response.json();
                this.couponValid = data.valid;
                if (data.valid) {
                    this.couponError = '';
                    this.discountType = data.discount_type;
                    this.discountValue = data.discount_value;
                    this.couponDiscount = data.discount_type === 'PERCENTAGE'
                        ? `${data.discount_value}% off`
                        : `${data.discount_value} XAF off`;
                } else {
                    this.couponError = data.error;
                    this.couponDiscount = null;
                }
            } catch (e) {
                this.couponError = 'Failed to validate coupon';
                this.couponValid = false;
            }
        },

        validateDeliveryEmails(event) {
            this.deliveryError = '';

            if (this.deliveryMethod !== 'EMAIL_INDIVIDUALLY') {
                return true;
            }

            const form = event.target;
            const emailInputs = form.querySelectorAll('input[name^="attendee_email_"]');
            const emails = [];
            const emptyEmails = [];

            emailInputs.forEach((input) => {
                const email = input.value.trim();
                if (email) {
                    emails.push(email.toLowerCase());
                } else {
                    emptyEmails.push(input);
                }
            });

            if (emptyEmails.length > 0) {
                this.deliveryError = 'Please fill in email addresses for all attendees when using individual delivery.';
                event.preventDefault();
                emptyEmails[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                emptyEmails[0].focus();
                return false;
            }

            const uniqueEmails = new Set(emails);
            if (uniqueEmails.size !== emails.length) {
                this.deliveryError = 'Each attendee must have a unique email address for individual delivery.';
                event.preventDefault();
                return false;
            }

            return true;
        }
    }));
});
