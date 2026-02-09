import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["sidebar", "overlay", "collapseIcon", "expandIcon"]
    static values = {
        open: { type: Boolean, default: false },
        collapsed: { type: Boolean, default: false }
    }

    connect() {
        const saved = localStorage.getItem('sidebarCollapsed');
        if (saved !== null) {
            this.collapsedValue = saved === 'true';
        }

        this.updateCollapsedUI(this.collapsedValue);
        delete document.documentElement.dataset.sidebarCollapsed;
    }

    openValueChanged(isOpen) {
        if (this.hasOverlayTarget) {
            this.overlayTarget.classList.toggle('hidden', !isOpen);
        }

        if (this.hasSidebarTarget) {
            if (isOpen) {
                this.sidebarTarget.classList.remove('-translate-x-full');
                this.sidebarTarget.classList.add('translate-x-0');
            } else {
                this.sidebarTarget.classList.add('-translate-x-full');
                this.sidebarTarget.classList.remove('translate-x-0');
            }
        }
    }

    collapsedValueChanged(isCollapsed) {
        localStorage.setItem('sidebarCollapsed', isCollapsed);

        this.updateCollapsedUI(isCollapsed);

        this.dispatch('collapsed', { detail: { collapsed: isCollapsed } });
    }

    updateCollapsedUI(isCollapsed) {
        if (this.hasSidebarTarget) {
            if (isCollapsed) {
                this.sidebarTarget.classList.remove('lg:w-64');
                this.sidebarTarget.classList.add('lg:w-[68px]');
            } else {
                this.sidebarTarget.classList.add('lg:w-64');
                this.sidebarTarget.classList.remove('lg:w-[68px]');
            }
        }

        if (this.hasCollapseIconTarget && this.hasExpandIconTarget) {
            this.collapseIconTarget.classList.toggle('hidden', isCollapsed);
            this.expandIconTarget.classList.toggle('hidden', !isCollapsed);
        }

        const textElements = this.element.querySelectorAll('.sidebar-text');
        textElements.forEach(el => {
            el.classList.toggle('hidden', isCollapsed);
        });

        const themeTextElements = this.element.querySelectorAll('.theme-text');
        themeTextElements.forEach(el => {
            el.classList.toggle('hidden', isCollapsed);
        });

        const sectionTitles = this.element.querySelectorAll('.sidebar-section-title');
        sectionTitles.forEach(el => {
            el.classList.toggle('hidden', isCollapsed);
        });

        const footer = this.element.querySelector('.sidebar-footer');
        if (footer) {
            footer.classList.toggle('hidden', isCollapsed);
        }

        const logoFull = this.element.querySelector('.sidebar-logo-full');
        const logoIcon = this.element.querySelector('.sidebar-logo-icon');
        if (logoFull && logoIcon) {
            logoFull.classList.toggle('hidden', isCollapsed);
            logoIcon.classList.toggle('hidden', !isCollapsed);
        }

        const modeFull = this.element.querySelector('.sidebar-mode-full');
        const modeIcon = this.element.querySelector('.sidebar-mode-icon');
        if (modeFull && modeIcon) {
            modeFull.classList.toggle('hidden', isCollapsed);
            modeIcon.classList.toggle('hidden', !isCollapsed);
        }

        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            if (isCollapsed) {
                mainContent.classList.remove('lg:pl-64');
                mainContent.classList.add('lg:pl-[68px]');
            } else {
                mainContent.classList.add('lg:pl-64');
                mainContent.classList.remove('lg:pl-[68px]');
            }
        }
    }

    toggleOpen() {
        this.openValue = !this.openValue;
    }

    close() {
        this.openValue = false;
    }

    toggleCollapse() {
        this.collapsedValue = !this.collapsedValue;
    }

    updateMainPadding(event) {
        const isCollapsed = event.detail.collapsed;
        const mainContent = this.element.querySelector('.main-content');
        if (mainContent) {
            if (isCollapsed) {
                mainContent.classList.remove('lg:pl-64');
                mainContent.classList.add('lg:pl-[68px]');
            } else {
                mainContent.classList.add('lg:pl-64');
                mainContent.classList.remove('lg:pl-[68px]');
            }
        }
    }
}
