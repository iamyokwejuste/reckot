import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["input", "fileName", "preview"]

    updateFileName(event) {
        const file = event?.target?.files?.[0];

        if (file && this.hasFileNameTarget) {
            this.fileNameTarget.textContent = file.name;

            if (this.hasPreviewTarget) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.previewTarget.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        } else if (this.hasFileNameTarget) {
            const emptyText = this.fileNameTarget.dataset.emptyText || 'No file chosen';
            this.fileNameTarget.textContent = emptyText;
        }
    }

    clearFile() {
        if (this.hasInputTarget) {
            this.inputTarget.value = '';
            this.updateFileName();
        }
    }
}
