import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["copyIcon", "checkIcon"]
    static values = {
        text: String,
        successMessage: { type: String, default: "Copied!" },
        errorMessage: { type: String, default: "Failed to copy" },
        successDuration: { type: Number, default: 2000 }
    }

    copy(event) {
        event.preventDefault()

        const textToCopy = this.hasTextValue ? this.textValue : this.element.dataset.clipboardText

        if (!textToCopy) {
            return
        }

        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                this.showSuccess(event.currentTarget)
            })
            .catch(err => {
                this.showError(event.currentTarget)
            })
    }

    showSuccess(button) {
        if (this.hasCopyIconTarget && this.hasCheckIconTarget) {
            this.copyIconTarget.classList.add('hidden');
            this.checkIconTarget.classList.remove('hidden');

            setTimeout(() => {
                this.copyIconTarget.classList.remove('hidden');
                this.checkIconTarget.classList.add('hidden');
            }, this.successDurationValue);
        } else {
            const originalHTML = button.innerHTML
            const originalClasses = button.className

            button.innerHTML = this.successMessageValue
            button.classList.add('bg-success', 'text-success-foreground')

            setTimeout(() => {
                button.innerHTML = originalHTML
                button.className = originalClasses

                requestAnimationFrame(() => {
                    if (typeof lucide !== 'undefined') {
                        lucide.createIcons()
                    }
                })
            }, this.successDurationValue)
        }
    }

    showError(button) {
        const originalHTML = button.innerHTML
        const originalClasses = button.className

        button.innerHTML = this.errorMessageValue
        button.classList.add('bg-destructive', 'text-destructive-foreground')

        setTimeout(() => {
            button.innerHTML = originalHTML
            button.className = originalClasses

            requestAnimationFrame(() => {
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons()
                }
            })
        }, this.successDurationValue)
    }
}
