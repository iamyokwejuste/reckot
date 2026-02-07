'use strict';

(function() {
    if (window._ReckotApp) return;

    const ReckotApp = {
        init() {
            this.setupEventListeners();
        },

        setupEventListeners() {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
            document.addEventListener('htmx:beforeRequest', () => this.onHTMXBeforeRequest());
            document.addEventListener('htmx:afterSettle', () => this.onHTMXAfterSettle());
        },

        onDOMReady() {
            this.initializeLucide();
            document.dispatchEvent(new CustomEvent('app:ready'));
        },

        onHTMXBeforeRequest() {
            const loader = document.getElementById('page-loader');
            if (loader && loader.style.display === 'none') {
                loader.style.display = 'flex';
                loader.style.opacity = '1';
            }
        },

        onHTMXAfterSettle() {
            requestAnimationFrame(() => {
                this.initializeLucide();
                this.hideLoader();
            });
        },

        hideLoader() {
            const loader = document.getElementById('page-loader');
            if (loader) {
                loader.style.opacity = '0';
                setTimeout(() => {
                    loader.style.display = 'none';
                }, 300);
            }
        },

        initializeLucide() {
            if (typeof lucide !== 'undefined') {
                try {
                    lucide.createIcons();
                } catch (error) {}
            }
        }
    };

    ReckotApp.init();
    window._ReckotApp = ReckotApp;

    document.addEventListener('showToast', (e) => {
        const { type, message } = e.detail;
        showToast(type, message);
    });

    window.showToast = function(type, message) {
        const container = document.getElementById('toast-container') || createToastContainer();
        const toast = document.createElement('div');
        toast.className = 'pointer-events-auto rounded-lg border shadow-lg p-4 flex items-start gap-3 transition-all duration-300 transform translate-x-4 opacity-0';

        const colors = {
            success: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-400',
            warning: 'bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-400',
            error: 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400',
            info: 'bg-card border-border'
        };

        const icons = {
            success: 'check-circle',
            warning: 'alert-triangle',
            error: 'x-circle',
            info: 'info'
        };

        toast.classList.add(...(colors[type] || colors.info).split(' '));
        toast.innerHTML = `
            <i data-lucide="${icons[type] || icons.info}" class="h-5 w-5 shrink-0 mt-0.5"></i>
            <p class="text-sm flex-1">${message}</p>
            <button onclick="this.parentElement.remove()" class="shrink-0 -mr-1 -mt-1 p-1 rounded hover:bg-black/5 dark:hover:bg-white/10">
                <i data-lucide="x" class="h-4 w-4"></i>
            </button>
        `;

        container.appendChild(toast);
        if (typeof lucide !== 'undefined') lucide.createIcons();

        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-4', 'opacity-0');
        });

        setTimeout(() => {
            toast.classList.add('translate-x-4', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    };

    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none';
        document.body.appendChild(container);
        return container;
    }
})();
