import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["item"]
    static values = {
        classes: { type: String, default: "animate-in" },
        once: { type: Boolean, default: true },
        threshold: { type: Number, default: 0.1 },
        mode: { type: String, default: "intersection" }
    }

    connect() {
        if (this.modeValue === "toast") {
            this.initializeToasts()
        } else {
            this.initializeIntersection()
        }
    }

    initializeIntersection() {
        this.observer = new IntersectionObserver(
            (entries) => this.handleIntersection(entries),
            {
                threshold: this.thresholdValue,
                rootMargin: "0px 0px -10% 0px"
            }
        );

        this.observer.observe(this.element);
    }

    initializeToasts() {
        if (!this.hasItemTarget) return

        this.itemTargets.forEach((toast, index) => {
            setTimeout(() => {
                toast.classList.remove('hidden')
                toast.classList.add('animate-in', 'slide-in-from-right')
            }, index * 100)

            setTimeout(() => {
                toast.classList.add('animate-out', 'slide-out-to-right')
                setTimeout(() => toast.remove(), 300)
            }, 5000 + (index * 100))
        })
    }

    dismiss(event) {
        const toast = event.currentTarget.closest('[data-animate-target="item"]')
        if (toast) {
            toast.classList.add('animate-out', 'slide-out-to-right')
            setTimeout(() => toast.remove(), 300)
        }
    }

    disconnect() {
        if (this.observer) {
            this.observer.disconnect()
        }
    }

    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const classes = this.classesValue.split(' ')
                this.element.classList.add(...classes)

                if (this.onceValue) {
                    this.observer.unobserve(this.element)
                }
            } else if (!this.onceValue) {
                const classes = this.classesValue.split(' ')
                this.element.classList.remove(...classes)
            }
        })
    }
}
