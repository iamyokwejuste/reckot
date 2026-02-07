import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static values = {
        message: { type: String, default: "Are you sure?" },
        confirmText: { type: String, default: "Delete" },
        cancelText: { type: String, default: "Cancel" }
    }

    confirm(event) {
        const confirmed = window.confirm(this.messageValue)

        if (!confirmed) {
            event.preventDefault()
            event.stopPropagation()
            return false
        }

        return true
    }

    async confirmAsync(event) {
        event.preventDefault()

        const confirmed = window.confirm(this.messageValue)

        if (confirmed && event.target.form) {
            event.target.form.submit()
        }
    }
}
