import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["content", "option", "formatOption", "reportTypeInput", "formatInput", "form", "optionsField"]
    static values = {
        open: { type: Boolean, default: false },
        initial: String
    }

    connect() {
        this.closeOthers = this.closeOthers.bind(this);
        this.clickOutsideBound = this.clickOutside.bind(this);
        document.addEventListener('dropdown:open', this.closeOthers);
        window.addEventListener('click', this.clickOutsideBound);

        if (this.initialValue && this.hasFormatOptionTarget) {
            this.formatOptionTargets.forEach(opt => {
                const isActive = opt.dataset.value === this.initialValue;
                if (isActive) {
                    opt.classList.remove('border-border', 'hover:border-muted-foreground');
                    opt.classList.add('border-foreground', 'bg-muted');
                } else {
                    opt.classList.remove('border-foreground', 'bg-muted');
                    opt.classList.add('border-border', 'hover:border-muted-foreground');
                }
            });
            if (this.hasFormatInputTarget) {
                this.formatInputTarget.value = this.initialValue;
            }
        }
    }

    disconnect() {
        document.removeEventListener('dropdown:open', this.closeOthers);
        window.removeEventListener('click', this.clickOutsideBound);
    }

    closeOthers(event) {
        if (event.detail.element !== this.element) {
            this.close();
        }
    }

    toggle() {
        this.openValue = !this.openValue;
    }

    open() {
        this.openValue = true;
    }

    close() {
        this.openValue = false;
    }

    clickOutside(event) {
        if (!this.element.contains(event.target)) {
            this.close();
        }
    }

    select(event) {
        const button = event.currentTarget;
        const value = button.dataset.value;

        if (this.hasOptionTarget && this.optionTargets.includes(button)) {
            this.optionTargets.forEach(opt => {
                opt.classList.remove('border-foreground', 'bg-muted');
                opt.classList.add('border-border');
            });
            button.classList.remove('border-border');
            button.classList.add('border-foreground', 'bg-muted');

            if (this.hasReportTypeInputTarget) {
                this.reportTypeInputTarget.value = value;
            }

            if (this.hasContentTarget) {
                this.contentTarget.classList.remove('hidden');
            }

            if (this.hasFormTarget) {
                this.formTarget.classList.remove('hidden');
            }
        }

        if (this.hasFormatOptionTarget && this.formatOptionTargets.includes(button)) {
            this.selectFormat(value);
        }
    }

    selectFormat(value) {
        this.formatOptionTargets.forEach(opt => {
            const isActive = opt.dataset.value === value;
            if (isActive) {
                opt.classList.remove('border-border', 'hover:border-muted-foreground');
                opt.classList.add('border-foreground', 'bg-muted');
            } else {
                opt.classList.remove('border-foreground', 'bg-muted');
                opt.classList.add('border-border', 'hover:border-muted-foreground');
            }
        });

        if (this.hasFormatInputTarget) {
            this.formatInputTarget.value = value;
        }

        if (this.hasFormTarget) {
            this.formTarget.classList.remove('hidden');
        }
    }

    handleFieldTypeChange(event) {
        const value = event.target.value;

        if (this.hasOptionsFieldTarget) {
            if (value === 'SELECT' || value === 'RADIO' || value === 'CHECKBOX') {
                this.optionsFieldTarget.classList.remove('hidden');
            } else {
                this.optionsFieldTarget.classList.add('hidden');
            }
        }
    }

    reset() {
        if (this.hasOptionTarget) {
            this.optionTargets.forEach(opt => {
                opt.classList.remove('border-foreground', 'bg-muted');
                opt.classList.add('border-border');
            });
        }

        if (this.hasFormatOptionTarget) {
            this.formatOptionTargets.forEach(opt => {
                opt.classList.remove('border-foreground', 'bg-muted');
                opt.classList.add('border-border', 'hover:border-muted-foreground');
            });
        }

        if (this.hasContentTarget) {
            this.contentTarget.classList.add('hidden');
        }

        if (this.hasFormTarget) {
            this.formTarget.classList.add('hidden');
        }

        if (this.hasReportTypeInputTarget) {
            this.reportTypeInputTarget.value = '';
        }

        if (this.hasFormatInputTarget) {
            this.formatInputTarget.value = 'PDF';
        }
    }

    openValueChanged() {
        if (this.openValue) {
            document.dispatchEvent(new CustomEvent('dropdown:open', {
                detail: { element: this.element }
            }));
        }

        if (this.hasContentTarget) {
            this.contentTarget.classList.toggle('hidden', !this.openValue);
            this.element.setAttribute('aria-expanded', this.openValue);
        }
    }
}
