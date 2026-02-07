import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["light", "dark"]

    connect() {
        this.updateLogos();

        this.observer = new MutationObserver(() => {
            this.updateLogos();
        });

        this.observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class']
        });
    }

    disconnect() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }

    updateLogos() {
        const isDark = document.documentElement.classList.contains('dark');

        if (this.hasLightTarget && this.hasDarkTarget) {
            if (isDark) {
                this.lightTarget.style.display = 'block';
                this.darkTarget.style.display = 'none';
            } else {
                this.lightTarget.style.display = 'none';
                this.darkTarget.style.display = 'block';
            }
        }
    }
}
