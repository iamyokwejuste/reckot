import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["ticketPrice", "ticketCount", "grossRevenue", "reckotFee", "netRevenue"]
    static values = {
        platformFee: { type: Number, default: 7 }
    }

    connect() {
        this.updateCalculations()
    }

    updateCalculations() {
        const ticketPrice = parseFloat(this.ticketPriceTarget.value) || 0
        const ticketCount = parseFloat(this.ticketCountTarget.value) || 0

        const grossRevenue = ticketPrice * ticketCount
        const reckotFee = Math.round(grossRevenue * this.platformFeeValue / 100)
        const netRevenue = grossRevenue - reckotFee

        this.grossRevenueTarget.textContent = this.formatCurrency(grossRevenue)
        this.reckotFeeTarget.textContent = '-' + this.formatCurrency(reckotFee)
        this.netRevenueTarget.textContent = this.formatCurrency(netRevenue)
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-FR').format(amount) + ' XAF'
    }
}
