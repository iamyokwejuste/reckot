import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["step1", "step2", "step3", "step4", "coverPreview", "progressBar"]

    static values = {
        currentStep: { type: Number, default: 1 },
        totalSteps: { type: Number, default: 4 },
        mode: String
    }

    connect() {
        this.eventType = 'IN_PERSON';
        this.errors = {};
        this.updateUI();
        this.toggleLocationFields();

        if (typeof window.initializeRichTextEditors === 'function') {
            window.initializeRichTextEditors(this.element);
        }

        requestAnimationFrame(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        });
    }

    currentStepValueChanged(newStep) {
        this.updateUI();

        if (newStep === 2) {
            this.initializeDatePickers();
        }
    }

    async handleCoverUpload(event) {
        const file = event.target.files[0];
        if (!file || !file.type.startsWith('image/')) return;

        try {
            const compressed = await this.compressImage(file);
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(compressed);
            event.target.files = dataTransfer.files;

            if (this.hasCoverPreviewTarget) {
                this.coverPreviewTarget.src = URL.createObjectURL(compressed);
                this.coverPreviewTarget.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Image compression failed:', error);
            if (this.hasCoverPreviewTarget) {
                this.coverPreviewTarget.src = URL.createObjectURL(file);
                this.coverPreviewTarget.classList.remove('hidden');
            }
        }
    }

    async compressImage(file, maxWidth = 1200, maxHeight = 630, quality = 0.85) {
        const img = await this.loadImage(file);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        let { width, height } = img;
        const aspectRatio = width / height;

        if (width > maxWidth) {
            width = maxWidth;
            height = width / aspectRatio;
        }

        if (height > maxHeight) {
            height = maxHeight;
            width = height * aspectRatio;
        }

        canvas.width = width;
        canvas.height = height;

        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0, width, height);

        const blob = await new Promise(resolve => {
            canvas.toBlob(resolve, 'image/jpeg', quality);
        });

        return new File([blob], file.name.replace(/\.\w+$/, '.jpg'), {
            type: 'image/jpeg'
        });
    }

    loadImage(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = reject;
                img.src = e.target.result;
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    updateEventType(event) {
        this.eventType = event.target.value;
        this.toggleLocationFields();
    }

    toggleLocationFields() {
        const locationFields = this.element.querySelector('[data-location-fields]');
        const onlineFields = this.element.querySelector('[data-online-fields]');

        if (!locationFields || !onlineFields) return;

        if (this.eventType === 'ONLINE') {
            locationFields.classList.add('hidden');
            onlineFields.classList.remove('hidden');
        } else if (this.eventType === 'IN_PERSON') {
            locationFields.classList.remove('hidden');
            onlineFields.classList.add('hidden');
        } else {
            locationFields.classList.remove('hidden');
            onlineFields.classList.remove('hidden');
        }
    }

    triggerFileInput() {
        const fileInput = this.element.querySelector('[data-cover-input]');
        if (fileInput) fileInput.click();
    }

    submitFormButton() {
        const form = this.element.querySelector('form');
        if (form) form.submit();
    }

    clearError(event) {
        const field = event.target.name;
        delete this.errors[field];
        const errorEl = this.element.querySelector(`[data-error="${field}"]`);
        if (errorEl) errorEl.classList.add('hidden');
    }

    nextStep() {
        let valid = false;

        switch (this.currentStepValue) {
            case 1: valid = this.validateStep1(); break;
            case 2: valid = this.validateStep2(); break;
            case 3: valid = this.validateStep3(); break;
            default: valid = true;
        }

        if (valid && this.currentStepValue < this.totalStepsValue) {
            this.currentStepValue++;
        }
    }

    prevStep() {
        this.errors = {};
        this.clearAllErrors();
        if (this.currentStepValue > 1) {
            this.currentStepValue--;
        }
    }

    validateStep1() {
        this.errors = {};

        if (this.modeValue === 'create') {
            const orgSelect = this.element.querySelector('[name="organization"]');
            if (!orgSelect?.value) {
                this.errors.organization = 'Please select an organization';
            }
        }

        const titleInput = this.element.querySelector('[name="title"]');
        if (!titleInput?.value.trim()) {
            this.errors.title = 'Event title is required';
        }

        const descInput = this.element.querySelector('[name="description"]');
        if (!descInput?.value.trim()) {
            this.errors.description = 'Description is required';
        }

        this.displayErrors();
        return Object.keys(this.errors).length === 0;
    }

    validateStep2() {
        this.errors = {};

        const startInput = this.element.querySelector('[name="start_at"]');
        if (!startInput?.value) {
            this.errors.start_at = 'Start date and time is required';
        }

        const endInput = this.element.querySelector('[name="end_at"]');
        if (!endInput?.value) {
            this.errors.end_at = 'End date and time is required';
        }

        this.displayErrors();
        return Object.keys(this.errors).length === 0;
    }

    validateStep3() {
        this.errors = {};

        if (this.eventType !== 'ONLINE') {
            const locationInput = this.element.querySelector('[name="location"]');
            if (!locationInput?.value.trim()) {
                this.errors.location = 'Address is required for in-person events';
            }
        }

        this.displayErrors();
        return Object.keys(this.errors).length === 0;
    }

    validateStep4() {
        this.errors = {};

        const emailInput = this.element.querySelector('[name="contact_email"]');
        const phoneInput = this.element.querySelector('[name="contact_phone"]');

        if (!emailInput?.value && !phoneInput?.value) {
            this.errors.contact = 'Please provide at least one contact method';
        }

        this.displayErrors();
        return Object.keys(this.errors).length === 0;
    }

    submitForm(event) {
        if (!this.validateStep4()) {
            event.preventDefault();
        }
    }

    updateUI() {
        [this.step1Target, this.step2Target, this.step3Target, this.step4Target].forEach((el, idx) => {
            el.classList.toggle('hidden', idx + 1 !== this.currentStepValue);
        });

        if (this.hasProgressBarTarget) {
            const progress = (this.currentStepValue / this.totalStepsValue) * 100;
            this.progressBarTarget.style.width = `${progress}%`;
        }

        const stepNumber = this.element.querySelector('[data-step-number]');
        if (stepNumber) stepNumber.textContent = this.currentStepValue;

        const stepLabels = ['Basic Info', 'Date & Time', 'Location', 'Details'];
        const stepLabel = this.element.querySelector('[data-step-label]');
        if (stepLabel) stepLabel.textContent = stepLabels[this.currentStepValue - 1];

        const prevButton = this.element.querySelector('[data-prev-button]');
        const nextButton = this.element.querySelector('[data-next-button]');
        const submitButton = this.element.querySelector('[data-submit-button]');

        if (prevButton) prevButton.classList.toggle('hidden', this.currentStepValue === 1);
        if (nextButton) nextButton.classList.toggle('hidden', this.currentStepValue === this.totalStepsValue);
        if (submitButton) submitButton.classList.toggle('hidden', this.currentStepValue !== this.totalStepsValue);

        const stepIndicators = this.element.querySelectorAll('[data-step-indicator]');
        stepIndicators.forEach((indicator, idx) => {
            if (idx + 1 === this.currentStepValue) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }

    displayErrors() {
        this.clearAllErrors();

        Object.entries(this.errors).forEach(([field, message]) => {
            const errorEl = this.element.querySelector(`[data-error="${field}"]`);
            if (errorEl) {
                errorEl.textContent = message;
                errorEl.classList.remove('hidden');
            }

            const fieldEl = this.element.querySelector(`[name="${field}"]`);
            if (fieldEl) {
                fieldEl.classList.add('border-destructive');
            }
        });
    }

    clearAllErrors() {
        const errorEls = this.element.querySelectorAll('[data-error]');
        errorEls.forEach(el => el.classList.add('hidden'));

        const inputs = this.element.querySelectorAll('input, select, textarea');
        inputs.forEach(input => input.classList.remove('border-destructive'));
    }

    initializeDatePickers() {
        const tryInit = (attempts = 0) => {
            if (attempts >= 5) return;

            setTimeout(() => {
                if (window.initDatePickers && !window.initDatePickers()) {
                    tryInit(attempts + 1);
                }
            }, 100 + (attempts * 100));
        };

        tryInit();
    }
}
