import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["emailForm", "phoneForm", "otpForm", "sendCodeBtn", "phoneInput"]

    static values = {
        loginMethod: { type: String, default: "email" },
        otpSent: { type: Boolean, default: false },
        otpLoading: { type: Boolean, default: false }
    }

    connect() {
        this.updateUI();
    }

    loginMethodValueChanged() {
        this.otpSentValue = false;
        this.updateUI();
    }

    otpSentValueChanged() {
        this.updateUI();
    }

    otpLoadingValueChanged() {
        this.updateUI();
    }

    switchToEmail() {
        this.loginMethodValue = "email";
    }

    switchToPhone() {
        this.loginMethodValue = "phone";
    }

    sendCode(event) {
        this.otpLoadingValue = true;
    }

    handleOtpResponse(event) {
        this.otpLoadingValue = false;
        if (event.detail.successful) {
            this.otpSentValue = true;
        }
    }

    backToPhone() {
        this.otpSentValue = false;
    }

    updateUI() {
        const emailTab = this.element.querySelector('[data-method="email"]');
        const phoneTab = this.element.querySelector('[data-method="phone"]');

        if (emailTab && phoneTab) {
            if (this.loginMethodValue === "email") {
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
            this.emailFormTarget.classList.toggle('hidden', this.loginMethodValue !== 'email');
        }

        if (this.hasPhoneFormTarget && this.hasOtpFormTarget) {
            const showPhoneForm = this.loginMethodValue === 'phone' && !this.otpSentValue;
            const showOtpForm = this.loginMethodValue === 'phone' && this.otpSentValue;

            this.phoneFormTarget.classList.toggle('hidden', !showPhoneForm);
            this.otpFormTarget.classList.toggle('hidden', !showOtpForm);
        }

        if (this.hasSendCodeBtnTarget) {
            const loadingContent = this.sendCodeBtnTarget.querySelector('[data-loading]');
            const normalContent = this.sendCodeBtnTarget.querySelector('[data-normal]');

            if (loadingContent && normalContent) {
                loadingContent.classList.toggle('hidden', !this.otpLoadingValue);
                normalContent.classList.toggle('hidden', this.otpLoadingValue);
            }

            this.sendCodeBtnTarget.disabled = this.otpLoadingValue;
        }
    }
}
