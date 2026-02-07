import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["exportModal", "withdrawModal"];
    static values = {
        availableBalance: Number
    };

    connect() {
        this.escapeHandler = this.handleEscape.bind(this);
    }

    open(event) {
        const modalName = event.currentTarget.dataset.modalName;
        const targetName = `${modalName}ModalTarget`;

        if (this[targetName]) {
            this[targetName].classList.remove("hidden");
            document.addEventListener("keydown", this.escapeHandler);
        }
    }

    close() {
        // Close all modals
        if (this.hasExportModalTarget) {
            this.exportModalTarget.classList.add("hidden");
        }
        if (this.hasWithdrawModalTarget) {
            this.withdrawModalTarget.classList.add("hidden");
        }
        document.removeEventListener("keydown", this.escapeHandler);
    }

    handleEscape(event) {
        if (event.key === "Escape") {
            this.close();
        }
    }

    disconnect() {
        document.removeEventListener("keydown", this.escapeHandler);
    }
}
