import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["tab", "panel"]
    static values = {
        active: String
    }

    connect() {
        if (!this.activeValue && this.hasTabTarget) {
            const firstTab = this.tabTargets[0];
            if (firstTab) {
                this.activeValue = firstTab.dataset.tab;
            }
        }
        this.updateUI();
    }

    activeValueChanged() {
        this.updateUI();
    }

    selectTab(event) {
        const tabName = event.currentTarget.dataset.tab;
        if (tabName) {
            this.activeValue = tabName;
        }
    }

    updateUI() {
        this.tabTargets.forEach(tab => {
            const isActive = tab.dataset.tab === this.activeValue;
            tab.classList.toggle('active', isActive);
            tab.setAttribute('aria-selected', isActive);
        });

        this.panelTargets.forEach(panel => {
            const isActive = panel.dataset.tabPanel === this.activeValue;
            panel.classList.toggle('hidden', !isActive);
            panel.setAttribute('aria-hidden', !isActive);
        });
    }
}
