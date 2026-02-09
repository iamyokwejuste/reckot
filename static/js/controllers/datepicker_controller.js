import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static values = {
        enableTime: { type: Boolean, default: false },
        time24hr: { type: Boolean, default: false },
        minDate: String,
        maxDate: String
    }

    connect() {
        this.initializeFlatpickr();
    }

    disconnect() {
        if (this.flatpickrInstance) {
            this.flatpickrInstance.destroy();
        }
    }

    initializeFlatpickr() {
        if (this.element._flatpickr) {
            try {
                this.element._flatpickr.destroy();
            } catch(e) {}
        }

        const config = {
            dateFormat: this.enableTimeValue ? "Y-m-d H:i" : "Y-m-d",
            altInput: true,
            altFormat: this.enableTimeValue ? "F j, Y \\a\\t h:i K" : "F j, Y",
            altInputClass: "input w-full pl-12 cursor-pointer",
            enableTime: this.enableTimeValue,
            time_24hr: this.time24hrValue,
            minuteIncrement: this.enableTimeValue ? 15 : 1,
            disableMobile: false,
            wrap: false,
            allowInput: false,
            clickOpens: true,
        };

        if (this.element.value) {
            config.defaultDate = this.element.value;
        }

        if (this.hasMinDateValue) {
            if (this.minDateValue === 'today') {
                config.minDate = 'today';
            } else {
                config.minDate = new Date(this.minDateValue);
            }
        }

        if (this.hasMaxDateValue) {
            config.maxDate = new Date(this.maxDateValue);
        }

        config.onChange = (selectedDates, dateStr) => {
            this.element.value = dateStr;
            this.element.dispatchEvent(new Event('change', { bubbles: true }));
        };

        try {
            this.flatpickrInstance = flatpickr(this.element, config);
        } catch(e) {
            console.error('Flatpickr initialization failed:', e);
        }

        // Reinitialize Lucide icons
        requestAnimationFrame(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        });
    }
}
