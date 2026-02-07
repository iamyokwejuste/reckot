import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["item", "content"]
    static values = {
        allowMultiple: { type: Boolean, default: false },
        activeItem: Number
    }

    connect() {
        this.updateUI();
    }

    toggle(event) {
        const button = event.currentTarget;
        const itemIndex = parseInt(button.dataset.itemIndex);

        if (this.activeItemValue === itemIndex) {
            this.activeItemValue = null;
        } else {
            this.activeItemValue = itemIndex;
        }
    }

    activeItemValueChanged() {
        this.updateUI();
    }

    updateUI() {
        this.contentTargets.forEach((content, index) => {
            const isActive = this.activeItemValue === (index + 1);
            const button = content.previousElementSibling;
            const icon = button.querySelector('[data-lucide]');

            content.classList.toggle('hidden', !isActive);

            button.setAttribute('aria-expanded', isActive);

            if (icon) {
                if (isActive) {
                    icon.classList.add('rotate-180');
                } else {
                    icon.classList.remove('rotate-180');
                }
            }
        });
    }
}
