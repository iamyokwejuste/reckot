import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";

const STORAGE_KEY = 'reckot_walkthrough_step';

const BASE_STEPS = [
    {
        target: '[data-walkthrough="discover"]',
        icon: 'compass',
        iconColor: 'text-blue-500',
        title: 'Discover events',
        description: 'Browse events by category, date, or location. Find what\'s happening near you.',
        arrow: 'down'
    },
    {
        target: '[data-walkthrough="theme-toggle"]',
        icon: 'moon',
        iconColor: 'text-indigo-500',
        title: 'Light & dark mode',
        description: 'Switch between light and dark themes to match your preference.',
        arrow: 'down'
    },
    {
        target: '[data-walkthrough="notifications"]',
        icon: 'bell',
        iconColor: 'text-yellow-500',
        title: 'Notifications',
        description: 'Get notified about ticket sales, event updates, check-ins, and important activity.',
        arrow: 'down'
    },
    {
        target: '[data-walkthrough="user-menu"]',
        icon: 'layout-dashboard',
        iconColor: 'text-purple-500',
        title: 'Your dashboard',
        description: 'Access events, organizations, analytics, payments, check-in, and CFP management all from here.',
        arrow: 'down'
    },
    {
        target: '[data-walkthrough="pricing-calculator"]',
        icon: 'calculator',
        iconColor: 'text-emerald-500',
        title: 'Pricing calculator',
        description: 'Enter your ticket price and quantity to see exactly what you earn. No hidden fees.',
        arrow: 'up',
        navigateTo: '/why-us/#pricing-calculator'
    },
];

const AI_STEPS = [
    {
        target: '[data-walkthrough="chat-header"]',
        icon: 'bot',
        iconColor: 'text-green-500',
        title: 'Meet the AI assistant',
        description: 'Your 24/7 helper. Ask questions, get recommendations, or create events through conversation.',
        arrow: 'right',
        openChatbot: true,
    },
    {
        target: '[data-walkthrough="chat-input"]',
        icon: 'message-square',
        iconColor: 'text-cyan-500',
        title: 'Chat to create',
        description: 'Type naturally, e.g. "Create a tech meetup in Douala next Friday". The AI handles the rest.',
        arrow: 'down',
        requiresChatbot: true,
    },
    {
        target: '[data-walkthrough="voice-input"]',
        icon: 'mic',
        iconColor: 'text-rose-500',
        title: 'Voice input',
        description: 'Tap the mic and speak. Describe your event by voice and the AI will set it all up.',
        arrow: 'right',
        requiresChatbot: true,
        closeChatbot: true,
    },
];

export default class extends Controller {
    static targets = ['overlay', 'spotlight', 'tooltip'];
    static values = { completeUrl: String, csrfToken: String, aiEnabled: Boolean };

    connect() {
        this.currentStep = 0;
        this._chatbotOpened = false;
        this._mobileMenuOpened = false;
        this._resizeHandler = () => this._repositionCurrent();
        this.steps = this._buildSteps();

        const saved = sessionStorage.getItem(STORAGE_KEY);
        if (saved !== null) {
            sessionStorage.removeItem(STORAGE_KEY);
            const step = parseInt(saved, 10);
            if (step >= 0 && step < this.steps.length) {
                setTimeout(() => this._resume(step), 600);
                return;
            }
        }

        setTimeout(() => this.start(), 1200);
    }

    disconnect() {
        window.removeEventListener('resize', this._resizeHandler);
    }

    start() {
        this.currentStep = 0;
        this.steps = this._buildSteps();
        this._showOverlay();
        this._showStep(0);
    }

    _resume(index) {
        this.currentStep = index;
        this._showOverlay();
        this._showStep(index);
    }

    _showOverlay() {
        this.overlayTarget.classList.remove('hidden');
        requestAnimationFrame(() => this.overlayTarget.classList.add('opacity-100'));
        window.addEventListener('resize', this._resizeHandler);
    }

    next() {
        this.tooltipTarget.classList.add('opacity-0', 'scale-95');
        setTimeout(() => this._showStep(this.currentStep + 1), 200);
    }

    previous() {
        if (this.currentStep > 0) {
            this.tooltipTarget.classList.add('opacity-0', 'scale-95');
            setTimeout(() => this._showStep(this.currentStep - 1), 200);
        }
    }

    skip() {
        sessionStorage.removeItem(STORAGE_KEY);
        this._closeMobileMenuIfOpen();
        this._closeChatbotIfOpen();
        this._complete();
    }

    _buildSteps() {
        if (this.aiEnabledValue) {
            return [...BASE_STEPS, ...AI_STEPS];
        }
        return [...BASE_STEPS];
    }

    _showStep(index) {
        if (index >= this.steps.length) {
            this._closeMobileMenuIfOpen();
            this._closeChatbotIfOpen();
            this._complete();
            return;
        }

        this.currentStep = index;
        const step = this.steps[index];

        if (step.navigateTo) {
            const target = this._findVisibleTarget(step.target);
            if (!target) {
                sessionStorage.setItem(STORAGE_KEY, index.toString());
                window.location.href = step.navigateTo;
                return;
            }
        }

        if (step.openChatbot) {
            this._openChatbot();
            setTimeout(() => this._renderStep(step, index), 400);
            return;
        }

        if (step.requiresChatbot && !this._chatbotOpened) {
            this._openChatbot();
            setTimeout(() => this._renderStep(step, index), 400);
            return;
        }

        if (!step.requiresChatbot && !step.openChatbot && this._chatbotOpened) {
            this._closeChatbotIfOpen();
        }

        this._renderStep(step, index);
    }

    _renderStep(step, index) {
        let target = this._findVisibleTarget(step.target);

        if (!target) {
            const hidden = document.querySelector(step.target);
            if (hidden && hidden.closest('[data-navbar-target="menu"]')) {
                this._openMobileMenu();
                setTimeout(() => {
                    const t = this._findVisibleTarget(step.target);
                    if (!t) { this._showStep(index + 1); return; }
                    this._positionStep(t, step, index);
                }, 350);
                return;
            }
            this._showStep(index + 1);
            return;
        }

        if (this._mobileMenuOpened && !target.closest('[data-navbar-target="menu"]')) {
            this._closeMobileMenuIfOpen();
            setTimeout(() => this._positionStep(target, step, index), 350);
            return;
        }

        this._positionStep(target, step, index);
    }

    _positionStep(target, step, index) {
        const rect = target.getBoundingClientRect();
        const inView = rect.top >= -50 && rect.bottom <= window.innerHeight + 50 && rect.width > 0;

        if (!inView) {
            target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
            setTimeout(() => {
                this._highlight(target);
                this._renderTooltip(target, step, index);
            }, 500);
        } else {
            this._highlight(target);
            this._renderTooltip(target, step, index);
        }
    }

    _findVisibleTarget(selector) {
        const elements = document.querySelectorAll(selector);
        for (const el of elements) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) return el;
        }
        return elements[0] || null;
    }

    _openMobileMenu() {
        const toggle = document.querySelector('[data-navbar-target="toggle"]');
        if (toggle) toggle.click();
        this._mobileMenuOpened = true;
    }

    _closeMobileMenuIfOpen() {
        if (!this._mobileMenuOpened) return;
        const menu = document.querySelector('[data-navbar-target="menu"]');
        if (menu && menu.style.display !== 'none') {
            const closeBtn = menu.querySelector('[data-action*="navbar#close"]');
            if (closeBtn) closeBtn.click();
        }
        this._mobileMenuOpened = false;
    }

    _openChatbot() {
        const container = document.getElementById('floating-chatbot-container');
        if (container && container.classList.contains('hidden')) {
            const trigger = document.querySelector('[data-chatbot-trigger]');
            if (trigger) trigger.click();
        }
        this._chatbotOpened = true;
    }

    _closeChatbotIfOpen() {
        if (!this._chatbotOpened) return;
        const container = document.getElementById('floating-chatbot-container');
        if (container && !container.classList.contains('hidden')) {
            const closeBtn = container.querySelector('[data-action*="chatbot#close"]');
            if (closeBtn) closeBtn.click();
        }
        this._chatbotOpened = false;
    }

    _highlight(el) {
        const rect = el.getBoundingClientRect();
        const pad = 12;
        const s = this.spotlightTarget;

        s.style.top = (rect.top - pad) + 'px';
        s.style.left = (rect.left - pad) + 'px';
        s.style.width = (rect.width + pad * 2) + 'px';
        s.style.height = (rect.height + pad * 2) + 'px';
        s.classList.remove('hidden');
    }

    _renderTooltip(el, step, index) {
        const rect = el.getBoundingClientRect();
        const total = this.steps.length;
        const progress = ((index + 1) / total) * 100;
        const isLast = index === total - 1;

        this.tooltipTarget.innerHTML = `
            <div class="mb-3 flex justify-center">
                <i data-lucide="${step.icon}" class="w-10 h-10 ${step.iconColor}"></i>
            </div>
            <h3 class="text-lg font-bold text-foreground mb-2">${step.title}</h3>
            <p class="text-muted-foreground text-sm leading-relaxed mb-5">${step.description}</p>
            <div class="flex items-center justify-between pt-4 border-t border-border">
                <div class="flex items-center gap-2 text-sm font-semibold text-primary">
                    <span>${index + 1} / ${total}</span>
                    <div class="w-14 h-1 bg-muted rounded-full overflow-hidden">
                        <div class="h-full bg-primary transition-all duration-300" style="width: ${progress}%"></div>
                    </div>
                </div>
                <div class="flex gap-2">
                    ${index > 0 ? `<button data-action="click->walkthrough#previous" class="px-4 py-2 bg-muted hover:bg-muted/80 text-foreground rounded-lg text-sm font-medium transition-colors">Back</button>` : ''}
                    <button data-action="click->walkthrough#${isLast ? 'skip' : 'next'}" class="px-5 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium transition-colors hover:opacity-90">${isLast ? 'Finish' : 'Next'}</button>
                </div>
            </div>
            ${this._arrowHTML(step.arrow)}
        `;

        if (typeof lucide !== 'undefined') lucide.createIcons();

        requestAnimationFrame(() => {
            const tt = this.tooltipTarget.getBoundingClientRect();
            let top, left;

            switch (step.arrow) {
                case 'up':
                    top = rect.bottom + 16;
                    left = rect.left + rect.width / 2 - tt.width / 2;
                    break;
                case 'down':
                    top = rect.top - tt.height - 16;
                    left = rect.left + rect.width / 2 - tt.width / 2;
                    break;
                case 'left':
                    top = rect.top + rect.height / 2 - tt.height / 2;
                    left = rect.right + 16;
                    break;
                case 'right':
                    top = rect.top + rect.height / 2 - tt.height / 2;
                    left = rect.left - tt.width - 16;
                    break;
            }

            top = Math.max(16, Math.min(top, window.innerHeight - tt.height - 16));
            left = Math.max(16, Math.min(left, window.innerWidth - tt.width - 16));

            this.tooltipTarget.style.top = top + 'px';
            this.tooltipTarget.style.left = left + 'px';
            this.tooltipTarget.classList.remove('opacity-0', 'scale-95');
            this.tooltipTarget.classList.add('opacity-100', 'scale-100');
        });
    }

    _arrowHTML(dir) {
        const color = getComputedStyle(document.documentElement).getPropertyValue('--card').trim();
        const fill = color ? `hsl(${color})` : 'hsl(var(--card))';
        const arrows = {
            up: `<div class="absolute -top-3 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[12px] border-r-[12px] border-b-[12px] border-transparent" style="border-bottom-color:${fill}"></div>`,
            down: `<div class="absolute -bottom-3 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[12px] border-r-[12px] border-t-[12px] border-transparent" style="border-top-color:${fill}"></div>`,
            left: `<div class="absolute -left-3 top-1/2 -translate-y-1/2 w-0 h-0 border-t-[12px] border-b-[12px] border-r-[12px] border-transparent" style="border-right-color:${fill}"></div>`,
            right: `<div class="absolute -right-3 top-1/2 -translate-y-1/2 w-0 h-0 border-t-[12px] border-b-[12px] border-l-[12px] border-transparent" style="border-left-color:${fill}"></div>`
        };
        return arrows[dir] || arrows.up;
    }

    _repositionCurrent() {
        const step = this.steps[this.currentStep];
        if (!step) return;
        const target = this._findVisibleTarget(step.target);
        if (target) this._highlight(target);
    }

    _complete() {
        sessionStorage.removeItem(STORAGE_KEY);
        this.tooltipTarget.classList.add('opacity-0', 'scale-95');
        this.overlayTarget.classList.remove('opacity-100');
        window.removeEventListener('resize', this._resizeHandler);

        setTimeout(() => {
            this.overlayTarget.classList.add('hidden');
            this.spotlightTarget.classList.add('hidden');
            this.tooltipTarget.classList.add('hidden');
        }, 300);

        if (this.completeUrlValue) {
            fetch(this.completeUrlValue, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfTokenValue,
                    'Content-Type': 'application/json',
                },
            }).catch(() => {});
        }
    }
}
