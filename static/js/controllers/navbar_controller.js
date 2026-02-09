import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["menu", "hamburger", "close", "notifications", "logoLight", "logoDark", "header"]

    connect() {
        this.bodyOverflowOriginal = document.body.style.overflow
        this.updateLogos()
        this.setupThemeObserver()

        this.scrollThreshold = 64
        this.navState = 'docked'
        this.ticking = false

        if (this.hasHeaderTarget && window.scrollY > this.scrollThreshold && window.innerWidth >= 768) {
            this.headerTarget.setAttribute('data-navbar-floating', '')
            const inset = this.measureNavInset() + 'px'
            this.headerTarget.style.left = inset
            this.headerTarget.style.right = inset
            this.headerTarget.style.paddingLeft = '1.5rem'
            this.headerTarget.style.paddingRight = '1.5rem'
            this.navState = 'floating'
        }
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

    onScroll() {
        if (!this.ticking) {
            requestAnimationFrame(() => {
                this.updateNavbarState()
                this.ticking = false
            })
            this.ticking = true
        }
    }

    measureNavInset() {
        const nav = this.headerTarget.querySelector('nav')
        if (!nav) return 8
        let contentWidth = 0
        for (const child of nav.children) {
            if (child.offsetWidth > 0) contentWidth += child.offsetWidth
        }
        contentWidth += 96
        return Math.max(8, (window.innerWidth - contentWidth) / 2)
    }

    updateNavbarState() {
        if (!this.hasHeaderTarget) return

        const header = this.headerTarget

        if (window.scrollY <= this.scrollThreshold || window.innerWidth < 768) {
            if (this.navState !== 'docked') {
                header.removeAttribute('data-navbar-floating')
                header.style.left = ''
                header.style.right = ''
                header.style.paddingLeft = ''
                header.style.paddingRight = ''
                this.navState = 'docked'
            }
        } else {
            if (this.navState !== 'floating') {
                header.setAttribute('data-navbar-floating', '')
                const inset = this.measureNavInset() + 'px'
                header.style.left = inset
                header.style.right = inset
                header.style.paddingLeft = '1.5rem'
                header.style.paddingRight = '1.5rem'
                this.navState = 'floating'
            }
        }
    }

    disconnect() {
        document.body.style.overflow = this.bodyOverflowOriginal
        if (this.observer) {
            this.observer.disconnect()
        }
    }
}
