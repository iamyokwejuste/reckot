import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["content"]
    static values = {
        open: { type: Boolean, default: false }
    }

    connect() {
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
            this.element.setAttribute('aria-expanded', this.openValue);
        }
    }
}
