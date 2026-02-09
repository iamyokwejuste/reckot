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
        if (this.hasDropdownTarget) {
            this.dropdownTarget.classList.toggle("hidden");
        }
    }

    selectMode(event) {
        const btn = event.currentTarget;
        const mode = btn.dataset.mode;

        btn.style.opacity = '0.5';
        btn.style.pointerEvents = 'none';

        const formData = new FormData();
        formData.append("mode", mode);

        fetch(this.switchUrlValue, {
            method: "POST",
            headers: {
                "X-CSRFToken": this.csrfTokenValue
            },
            body: formData
        }).then(response => {
            if (response.ok || response.redirected) {
                window.location.reload();
            } else {
                btn.style.opacity = '';
                btn.style.pointerEvents = '';
            }
        }).catch(() => {
            btn.style.opacity = '';
            btn.style.pointerEvents = '';
        });
    }

    clickOutside(event) {
        if (this.hasDropdownTarget && !this.element.contains(event.target)) {
            this.dropdownTarget.classList.add("hidden");
        }
    }
}
