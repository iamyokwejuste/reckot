import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["content", "trigger", "dropdown", "menu", "chevron", "hiddenInput", "search", "option"]
    static values = {
        value: String,
        label: String,
        open: { type: Boolean, default: false }
    }

    connect() {
        super.connect?.();
        if (this.hasValueValue && this.hasLabelValue) {
            this.selectByValue(this.valueValue, this.labelValue);
        }
        this.closeOthers = this.closeOthers.bind(this);
        this.clickOutsideBound = this.clickOutside.bind(this);
        document.addEventListener('dropdown:open', this.closeOthers);
        window.addEventListener('click', this.clickOutsideBound);
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

    selectOption(event) {
        const option = event.currentTarget;
        const value = option.dataset.value;
        const label = option.dataset.label;

        if (this.hasHiddenInputTarget) {
            this.hiddenInputTarget.value = value;
            this.hiddenInputTarget.dispatchEvent(new Event('change', { bubbles: true }));
        }

        if (this.hasTriggerTarget) {
            const valueSpan = this.triggerTarget.querySelector('.custom-select-value');
            if (valueSpan) {
                valueSpan.textContent = label;
                valueSpan.classList.remove('custom-select-placeholder');
            }
        }

        this.updateSelectedState(option);
        this.close();
    }

    select(event) {
        this.selectOption(event);
    }

    submitForm() {
        const form = this.element.closest('form');
        if (form) form.submit();
    }

    updateSelectedState(selectedOption) {
        this.optionTargets.forEach(opt => {
            const isSelected = opt === selectedOption;
            opt.classList.toggle('custom-select-option-selected', isSelected);

            const checkIcon = opt.querySelector('.custom-select-check');
            if (checkIcon) {
                checkIcon.classList.toggle('hidden', !isSelected);
            }
        });
    }

    selectByValue(value, label) {
        const option = this.optionTargets.find(opt => opt.dataset.value === value);
        if (option) {
            if (this.hasHiddenInputTarget) {
                this.hiddenInputTarget.value = value;
            }

            if (this.hasTriggerTarget) {
                const valueSpan = this.triggerTarget.querySelector('.custom-select-value');
                if (valueSpan) {
                    valueSpan.textContent = label;
                    valueSpan.classList.remove('custom-select-placeholder');
                }
            }

            this.updateSelectedState(option);
        }
    }

    updateSearch(event) {
        const query = event.target.value.toLowerCase();
        this.optionTargets.forEach(option => {
            const text = option.textContent.toLowerCase();
            option.classList.toggle('hidden', !text.includes(query));
        });
    }

    stopPropagation(event) {
        event.stopPropagation();
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

    openValueChanged() {
        if (this.openValue) {
            document.dispatchEvent(new CustomEvent('dropdown:open', {
                detail: { element: this.element }
            }));
        }

        if (this.hasContentTarget) {
            this.contentTarget.classList.toggle('hidden', !this.openValue);
        }
        if (this.hasDropdownTarget) {
            this.dropdownTarget.classList.toggle('hidden', !this.openValue);
        }
        if (this.hasMenuTarget) {
            this.menuTarget.classList.toggle('hidden', !this.openValue);
        }
        if (this.hasChevronTarget) {
            this.chevronTarget.style.transform = this.openValue ? 'rotate(180deg)' : 'rotate(0deg)';
        }
        this.element.setAttribute('aria-expanded', this.openValue);
    }
}
