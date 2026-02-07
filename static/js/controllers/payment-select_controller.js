import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["phoneInput", "carrierBadge", "methodRadio", "paymentMethodInput"]

    connect() {
        const mtnPrefixes = ['67', '650', '651', '652', '653', '654', '680', '681', '682', '683'];
        const orangePrefixes = ['640', '655', '656', '657', '658', '659', '686', '687', '688', '689', '69'];

        this.mtnPrefixes = mtnPrefixes;
        this.orangePrefixes = orangePrefixes;
    }

    updateMethod(event) {
        const paymentMethod = event.currentTarget.getAttribute('data-payment-method');
        if (paymentMethod && this.hasPaymentMethodInputTarget) {
            this.paymentMethodInputTarget.value = paymentMethod;
        }
    }

    updateCarrier(event) {
        if (!this.hasCarrierBadgeTarget) return;

        let phone = event.target.value.replace(/\D/g, '');
        if (phone.startsWith('237')) phone = phone.substring(3);

        if (phone.length < 2) {
            this.carrierBadgeTarget.classList.add('hidden');
            return;
        }

        let carrier = '';
        for (const p of this.mtnPrefixes) {
            if (phone.startsWith(p)) {
                carrier = 'MTN';
                break;
            }
        }
        if (!carrier) {
            for (const p of this.orangePrefixes) {
                if (phone.startsWith(p)) {
                    carrier = 'ORANGE';
                    break;
                }
            }
        }

        if (carrier) {
            this.carrierBadgeTarget.textContent = carrier;
            this.carrierBadgeTarget.className = 'carrier-badge text-xs font-medium px-2 py-1 rounded-full ';
            this.carrierBadgeTarget.className += carrier === 'MTN'
                ? 'bg-yellow-500/20 text-yellow-600'
                : 'bg-orange-500/20 text-orange-600';
            this.carrierBadgeTarget.classList.remove('hidden');
        } else {
            this.carrierBadgeTarget.classList.add('hidden');
        }
    }
}
