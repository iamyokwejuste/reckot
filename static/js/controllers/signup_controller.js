import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["emailForm", "phoneForm", "phoneRequest", "phoneVerify"]

    static values = {
        method: { type: String, default: "email" }
    }

    connect() {
        this.updateUI();
    }

    methodValueChanged() {
        this.updateUI();
    }

    setMethod(event) {
        const method = event.currentTarget.dataset.method;
        if (method) {
            this.methodValue = method;
        }
    }

    handleOtpResponse(event) {
        if (event.detail.successful) {
            if (this.hasPhoneRequestTarget && this.hasPhoneVerifyTarget) {
                this.phoneRequestTarget.classList.add('hidden');
                this.phoneVerifyTarget.classList.remove('hidden');

                const phoneInput = this.phoneRequestTarget.querySelector('input[name="phone_number"]');
                const phoneHidden = this.phoneVerifyTarget.querySelector('#phone_number_hidden');
                if (phoneInput && phoneHidden) {
                    phoneHidden.value = phoneInput.value;
                }
            }
        }
    }

    backToPhone() {
        if (this.hasPhoneRequestTarget && this.hasPhoneVerifyTarget) {
            this.phoneVerifyTarget.classList.add('hidden');
            this.phoneRequestTarget.classList.remove('hidden');
        }
    }

    updateUI() {
        const emailTab = this.element.querySelector('[data-method="email"]');
        const phoneTab = this.element.querySelector('[data-method="phone"]');

        if (emailTab && phoneTab) {
            if (this.methodValue === "email") {
                emailTab.classList.add('bg-background', 'text-foreground', 'shadow-sm');
                emailTab.classList.remove('text-muted-foreground', 'hover:text-foreground');
                phoneTab.classList.remove('bg-background', 'text-foreground', 'shadow-sm');
                phoneTab.classList.add('text-muted-foreground', 'hover:text-foreground');
            } else {
                phoneTab.classList.add('bg-background', 'text-foreground', 'shadow-sm');
                phoneTab.classList.remove('text-muted-foreground', 'hover:text-foreground');
                emailTab.classList.remove('bg-background', 'text-foreground', 'shadow-sm');
                emailTab.classList.add('text-muted-foreground', 'hover:text-foreground');
            }
        }

        if (this.hasEmailFormTarget) {
            this.emailFormTarget.classList.toggle('hidden', this.methodValue !== 'email');
        }

        if (this.hasPhoneFormTarget) {
            this.phoneFormTarget.classList.toggle('hidden', this.methodValue !== 'phone');
        }

        requestAnimationFrame(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        });
    }
}
