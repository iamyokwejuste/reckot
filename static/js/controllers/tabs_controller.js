import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["tab", "panel"]
    static values = {
        initial: String
    }

    connect() {
        const initialValue = this.initialValue || this.tabTargets[0]?.dataset.tabsTabValue;
        if (initialValue) {
            this.select({ currentTarget: this.tabTargets.find(t => t.dataset.tabsTabValue === initialValue) });
        }
    }

    select(event) {
        const button = event.currentTarget;
        const tabValue = button.dataset.tabsTabValue;

        this.tabTargets.forEach(tab => {
            const isActive = tab.dataset.tabsTabValue === tabValue;
            if (isActive) {
                tab.classList.remove('text-muted-foreground', 'hover:text-foreground');
                tab.classList.add('bg-background', 'shadow-sm', 'text-foreground');
            } else {
                tab.classList.remove('bg-background', 'shadow-sm', 'text-foreground');
                tab.classList.add('text-muted-foreground', 'hover:text-foreground');
            }
            tab.setAttribute('aria-selected', isActive);
        });

        if (this.hasPanelTarget) {
            this.panelTargets.forEach(panel => {
                const isActive = panel.dataset.tabPanel === tabValue;
                panel.classList.toggle('hidden', !isActive);
                panel.setAttribute('aria-hidden', !isActive);
            });
        }
    }
}
