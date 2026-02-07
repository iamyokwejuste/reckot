import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export class BaseController extends Controller {
    show(target) {
        if (target) target.classList.remove('hidden');
    }

    hide(target) {
        if (target) target.classList.add('hidden');
    }

    toggle(target) {
        if (target) target.classList.toggle('hidden');
    }

    addClass(element, ...classes) {
        if (element) element.classList.add(...classes);
    }

    removeClass(element, ...classes) {
        if (element) element.classList.remove(...classes);
    }

    toggleClass(element, ...classes) {
        if (element) classes.forEach(cls => element.classList.toggle(cls));
    }

    dispatch(eventName, detail = {}) {
        this.element.dispatchEvent(new CustomEvent(eventName, {
            detail,
            bubbles: true,
            cancelable: true
        }));
    }

    on(eventName, handler, options = {}) {
        this.element.addEventListener(eventName, handler, options);
    }

    off(eventName, handler, options = {}) {
        this.element.removeEventListener(eventName, handler, options);
    }
}

export class BaseToggleController extends BaseController {
    static targets = ["content"]
    static values = {
        open: { type: Boolean, default: false }
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
        if (this.hasContentTarget) {
            this.contentTarget.classList.toggle('hidden', !this.openValue);
            this.element.setAttribute('aria-expanded', this.openValue);
            this.dispatch(this.openValue ? 'opened' : 'closed');
        }
    }
}
