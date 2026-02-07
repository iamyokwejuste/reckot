import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["menu", "toggle", "hamburger", "close", "notifications"]

    connect() {
        this.bodyOverflowOriginal = document.body.style.overflow
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

        this.updateToggleIcon(true)
        this.menuTarget.style.display = 'flex'

        if (this.hasToggleTarget) {
            this.toggleTarget.setAttribute('aria-expanded', 'true')
        }

        document.body.style.overflow = 'hidden'

        requestAnimationFrame(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons()
            }
        })
    }

    close() {
        if (!this.hasMenuTarget) return

        this.updateToggleIcon(false)
        this.menuTarget.style.display = 'none'

        if (this.hasToggleTarget) {
            this.toggleTarget.setAttribute('aria-expanded', 'false')
        }

        document.body.style.overflow = this.bodyOverflowOriginal
    }

    openNotifications() {
        if (!this.hasNotificationsTarget) return

        this.notificationsTarget.style.display = 'flex'
        document.body.style.overflow = 'hidden'

        // Trigger notifications fetch
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

    updateToggleIcon(isOpen) {
        if (this.hasHamburgerTarget && this.hasCloseTarget) {
            this.hamburgerTarget.style.display = isOpen ? 'none' : 'block'
            this.closeTarget.style.display = isOpen ? 'block' : 'none'
        }
    }

    disconnect() {
        document.body.style.overflow = this.bodyOverflowOriginal
    }
}
