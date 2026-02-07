import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["menu", "hamburger", "close", "notifications", "logoLight", "logoDark"]

    connect() {
        this.bodyOverflowOriginal = document.body.style.overflow
        this.updateLogos()
        this.setupThemeObserver()
    }

    setupThemeObserver() {
        this.observer = new MutationObserver(() => {
            this.updateLogos()
        })
        this.observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class']
        })
    }

    toggle() {
        if (this.hasMenuTarget) {
            const isOpen = this.menuTarget.style.display === 'flex'
            if (isOpen) {
                this.close()
            } else {
                this.open()
            }
        }
    }

    open() {
        if (!this.hasMenuTarget) return

        this.updateMenuIcon(true)
        this.menuTarget.style.display = 'flex'
        document.body.style.overflow = 'hidden'

        requestAnimationFrame(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons()
            }
        })
    }

    close() {
        if (!this.hasMenuTarget) return

        this.updateMenuIcon(false)
        this.menuTarget.style.display = 'none'
        document.body.style.overflow = this.bodyOverflowOriginal
    }

    openNotifications() {
        if (!this.hasNotificationsTarget) return

        this.notificationsTarget.style.display = 'flex'
        document.body.style.overflow = 'hidden'

        const controller = this.notificationsTarget.querySelector('[data-controller~="notifications"]')
        if (controller && window.Stimulus) {
            const instance = window.Stimulus.getControllerForElementAndIdentifier(
                this.notificationsTarget,
                'notifications'
            )
            if (instance && typeof instance.fetchNotifications === 'function') {
                instance.fetchNotifications()
            }
        }

        requestAnimationFrame(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons()
            }
        })
    }

    closeNotifications() {
        if (!this.hasNotificationsTarget) return

        this.notificationsTarget.style.display = 'none'
        document.body.style.overflow = this.bodyOverflowOriginal
    }

    updateMenuIcon(isOpen) {
        if (this.hasHamburgerTarget && this.hasCloseTarget) {
            this.hamburgerTarget.style.display = isOpen ? 'none' : 'block'
            this.closeTarget.style.display = isOpen ? 'block' : 'none'
        }
    }

    updateLogos() {
        const isDark = document.documentElement.classList.contains('dark')

        this.logoLightTargets.forEach(logo => {
            logo.style.display = isDark ? 'block' : 'none'
        })

        this.logoDarkTargets.forEach(logo => {
            logo.style.display = isDark ? 'none' : 'block'
        })
    }

    disconnect() {
        document.body.style.overflow = this.bodyOverflowOriginal
        if (this.observer) {
            this.observer.disconnect()
        }
    }
}
