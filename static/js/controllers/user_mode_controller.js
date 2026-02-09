import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["dropdown", "modeOption"]
    static values = {
        switchUrl: String,
        csrfToken: String
    }

    connect() {
        this.clickOutsideBound = this.clickOutside.bind(this);
        window.addEventListener("click", this.clickOutsideBound);
    }

    disconnect() {
        window.removeEventListener("click", this.clickOutsideBound);
    }

    toggle(event) {
        event.stopPropagation();
        this.dropdownTarget.classList.toggle("hidden");
    }

    selectMode(event) {
        const mode = event.currentTarget.dataset.mode;

        fetch(this.switchUrlValue, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": this.csrfTokenValue
            },
            body: JSON.stringify({ mode: mode })
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            }
        }).catch(() => {});
    }

    clickOutside(event) {
        if (!this.element.contains(event.target)) {
            this.dropdownTarget.classList.add("hidden");
        }
    }
}
