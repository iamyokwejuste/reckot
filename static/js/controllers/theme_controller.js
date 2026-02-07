import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    connect() {
        const mode = localStorage.getItem('theme') || 'system';
        this.mode = mode;
        this.updateTheme();

        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
            if (this.mode === 'system') {
                this.updateTheme();
            }
        });
    }

    updateTheme() {
        let isDark;
        if (this.mode === 'system') {
            isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        } else {
            isDark = this.mode === 'dark';
        }

        if (isDark) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    setMode(event) {
        this.mode = event.params.mode || event.currentTarget.dataset.mode;
        localStorage.setItem('theme', this.mode);
        this.updateTheme();
    }

    toggleMode() {
        const isDark = document.documentElement.classList.contains('dark');
        this.mode = isDark ? 'light' : 'dark';
        localStorage.setItem('theme', this.mode);
        this.updateTheme();
    }
}
