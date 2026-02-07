import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["container"];

    connect() {
        this.escapeHandler = this.handleEscape.bind(this);
    }

    open(event) {
        event?.preventDefault();
        if (this.hasContainerTarget) {
            this.containerTarget.classList.remove("hidden");
            document.addEventListener("keydown", this.escapeHandler);
            document.body.style.overflow = "hidden";
        } else {
            this.element.classList.remove("hidden");
            document.addEventListener("keydown", this.escapeHandler);
            document.body.style.overflow = "hidden";
        }
    }

    close(event) {
        event?.preventDefault();
        if (this.hasContainerTarget) {
            this.containerTarget.classList.add("hidden");
        } else {
            this.element.classList.add("hidden");
        }
        document.removeEventListener("keydown", this.escapeHandler);
        document.body.style.overflow = "";
    }

    handleEscape(event) {
        if (event.key === "Escape") {
            this.close();
        }
    }

    stopPropagation(event) {
        event.stopPropagation();
    }

    print(event) {
        event?.preventDefault();
        window.print();
    }

    disconnect() {
        document.removeEventListener("keydown", this.escapeHandler);
        document.body.style.overflow = "";
    }
}
