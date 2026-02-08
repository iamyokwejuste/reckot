import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["amount", "phone", "commission", "receive", "preview", "submit", "form", "status", "formFields", "error"]
    static values = {
        fee: { type: Number, default: 7 },
        max: Number
    }

    connect() {
        this.update()
    }

    update() {
        const raw = parseFloat(this.amountTarget.value) || 0
        const amount = Math.max(0, raw)
        if (raw < 0) this.amountTarget.value = 0
        const commission = Math.round(amount * this.feeValue / 100)
        const receive = amount - commission

        this.commissionTarget.textContent = this.formatCurrency(commission)
        this.receiveTarget.textContent = this.formatCurrency(receive)

        if (amount > 0) {
            this.previewTarget.classList.remove("hidden")
        } else {
            this.previewTarget.classList.add("hidden")
        }

        if (this.hasSubmitTarget) {
            this.submitTarget.disabled = amount < 200 || amount > this.maxValue
        }

        this.clearError()
    }

    async submit(event) {
        event.preventDefault()
        this.clearError()

        const form = this.formTarget
        const submitBtn = this.submitTarget
        const formData = new FormData(form)

        const phone = (formData.get("phone_number") || "").replace(/\s+/g, "").trim()
        formData.set("phone_number", phone)

        submitBtn.disabled = true
        const originalHtml = submitBtn.innerHTML
        submitBtn.innerHTML = `<svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg><span>Processing...</span>`

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })

            const data = await response.json()

            if (data.success) {
                this.showSuccess(data)
            } else {
                const msg = data.error || "Something went wrong. Please try again."
                this.showError(msg)
                if (window.showToast) window.showToast("error", msg)
                submitBtn.disabled = false
                submitBtn.innerHTML = originalHtml
            }
        } catch (err) {
            const msg = "Could not reach the server. Please check your connection and try again."
            this.showError(msg)
            if (window.showToast) window.showToast("error", msg)
            submitBtn.disabled = false
            submitBtn.innerHTML = originalHtml
        }
    }

    showError(message) {
        if (this.hasErrorTarget) {
            this.errorTarget.textContent = message
            this.errorTarget.classList.remove("hidden")
        }
    }

    clearError() {
        if (this.hasErrorTarget) {
            this.errorTarget.textContent = ""
            this.errorTarget.classList.add("hidden")
        }
    }

    showSuccess(data) {
        this.formFieldsTarget.classList.add("hidden")
        this.statusTarget.innerHTML = `
            <div class="text-center py-6">
                <div class="w-14 h-14 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-7 h-7 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                </div>
                <h3 class="text-lg font-semibold mb-2">Withdrawal Requested!</h3>
                <p class="text-sm text-muted-foreground mb-4">Your withdrawal of ${this.formatCurrency(data.net_amount)} has been submitted. Reference: ${data.reference}</p>
                <p class="text-xs text-muted-foreground">You will receive the funds shortly.</p>
            </div>
        `
        this.statusTarget.classList.remove("hidden")
    }

    dismiss() {
        document.getElementById('withdrawModal').classList.add('hidden')
        document.body.style.overflow = ''

        this.statusTarget.innerHTML = ''
        this.statusTarget.classList.add('hidden')
        this.formFieldsTarget.classList.remove('hidden')
        this.amountTarget.value = ''
        this.clearError()
        this.update()
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-FR').format(amount) + ' XAF'
    }
}
