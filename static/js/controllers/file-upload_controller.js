import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["input", "fileName", "placeholder", "fileInfo"]

    updateFileName(event) {
        const file = event.target.files[0];
        if (file && this.hasFileNameTarget) {
            this.fileNameTarget.textContent = file.name;
            if (this.hasPlaceholderTarget) {
                this.placeholderTarget.classList.add('hidden');
            }
            if (this.hasFileInfoTarget) {
                this.fileInfoTarget.classList.remove('hidden');
            }
            if (window.lucide) lucide.createIcons();
        }
    }

    clearFile() {
        if (this.hasInputTarget) {
            this.inputTarget.value = '';
        }
        if (this.hasPlaceholderTarget) {
            this.placeholderTarget.classList.remove('hidden');
        }
        if (this.hasFileInfoTarget) {
            this.fileInfoTarget.classList.add('hidden');
        }
    }
}
