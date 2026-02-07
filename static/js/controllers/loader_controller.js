import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["logoLight", "logoDark", "spinner"]

    connect() {
        this.applyTheme()
        this.setupHideTimer()
    }

    applyTheme() {
        const mode = localStorage.getItem('theme') || 'system'
        const isDark = mode === 'dark' ||
                      (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

        if (isDark) {
            document.documentElement.classList.add('dark')
            if (this.hasLogoDarkTarget) {
                this.logoDarkTarget.style.display = 'block'
            }
            this.element.style.backgroundColor = '#09090b'
            if (this.hasSpinnerTarget) {
                this.spinnerTarget.style.color = '#fafafa'
            }
        } else {
            document.documentElement.classList.remove('dark')
            if (this.hasLogoLightTarget) {
                this.logoLightTarget.style.display = 'block'
            }
            this.element.style.backgroundColor = '#fafafa'
            if (this.hasSpinnerTarget) {
                this.spinnerTarget.style.color = '#09090b'
            }
        }
    }

    setupHideTimer() {
        // Hide loader after DOM is ready
        const hideLoader = () => {
            this.element.style.opacity = '0'
            setTimeout(() => {
                this.element.style.display = 'none'
            }, 300)
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(hideLoader, 300)
            })
        } else {
            setTimeout(hideLoader, 300)
        }

        // Also listen for Stimulus ready
        document.addEventListener('stimulus:ready', () => {
            setTimeout(hideLoader, 100)
        })
    }

    hide() {
        this.element.style.opacity = '0'
        setTimeout(() => {
            this.element.style.display = 'none'
        }, 300)
    }

    show() {
        this.element.style.display = 'flex'
        this.element.style.opacity = '1'
    }
}
