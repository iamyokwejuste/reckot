'use strict';

window.ReckotWalkthrough = {
    steps: [
        {
            target: '[data-walkthrough="chat-button"]',
            icon: 'message-circle',
            iconColor: 'text-green-500',
            title: 'Welcome to Reckot AI!',
            description: 'Meet your <span class="bg-yellow-100 px-2 py-0.5 rounded font-semibold">24/7 AI Assistant</span>. Click this chat icon anytime to ask questions, get help, or create content instantly.',
            arrow: 'down'
        },
        {
            target: '[data-walkthrough="create-event"]',
            icon: 'plus-circle',
            iconColor: 'text-purple-500',
            title: 'Create Events in Seconds',
            description: 'Click here to create a new event. AI will help you with descriptions, pricing, and everything else. <span class="bg-yellow-100 px-2 py-0.5 rounded font-semibold">8 hours → 10 minutes!</span>',
            arrow: 'up'
        },
        {
            target: '[data-walkthrough="templates"]',
            icon: 'layers',
            iconColor: 'text-blue-500',
            title: 'Community Templates',
            description: 'Choose from <span class="bg-yellow-100 px-2 py-0.5 rounded font-semibold">6 African event types</span> (Church, Village, Festival, University, Market, Youth). AI generates culturally appropriate content.',
            arrow: 'left'
        },
        {
            target: '[data-walkthrough="scanner"]',
            icon: 'camera',
            iconColor: 'text-indigo-500',
            title: 'Smart Event Scanner',
            description: 'Have a poster? <span class="bg-yellow-100 px-2 py-0.5 rounded font-semibold">Take a photo</span> and AI extracts ALL details - title, date, location, prices. It even analyzes competitors!',
            arrow: 'up'
        },
        {
            target: '[data-walkthrough="events-list"]',
            icon: 'bar-chart-2',
            iconColor: 'text-yellow-500',
            title: 'Your Events Dashboard',
            description: 'All your events are here. Click any event to access the <span class="bg-yellow-100 px-2 py-0.5 rounded font-semibold">AI Concierge</span> - 5 expert agents that optimize your event.',
            arrow: 'right'
        },
        {
            target: '[data-walkthrough="concierge"]',
            icon: 'users',
            iconColor: 'text-pink-500',
            title: 'Multi-Agent Concierge',
            description: 'The magic feature! <span class="bg-yellow-100 px-2 py-0.5 rounded font-semibold">5 AI specialists</span> (Analyst, Marketer, Support, Fraud Detective, Pricing Expert) review your event together.',
            arrow: 'down'
        },
        {
            target: '[data-walkthrough="low-bandwidth"]',
            icon: 'smartphone',
            iconColor: 'text-orange-500',
            title: 'Low-Bandwidth Mode',
            description: 'On mobile data? Enable this to <span class="bg-yellow-100 px-2 py-0.5 rounded font-semibold">save 50% data</span>. AI works faster and cheaper - perfect for areas with slow connection.',
            arrow: 'left'
        },
        {
            target: '[data-walkthrough="metrics"]',
            icon: 'trending-up',
            iconColor: 'text-red-500',
            title: 'AI Usage Dashboard',
            description: 'Track your AI usage, costs, and <span class="bg-yellow-100 px-2 py-0.5 rounded font-semibold">time saved</span>. See exactly how much AI helps your business.',
            arrow: 'up'
        },
        {
            target: '[data-walkthrough="chat-button"]',
            icon: 'rocket',
            iconColor: 'text-green-500',
            title: 'You\'re All Set!',
            description: 'Try clicking the chat icon and ask: <span class="bg-yellow-100 px-2 py-0.5 rounded font-semibold">"How do I create my first event?"</span> - AI will guide you through everything!',
            arrow: 'down'
        }
    ],

    currentStep: 0,
    overlay: null,
    spotlight: null,
    tooltip: null,
    skipButton: null,

    init() {
        this.overlay = document.getElementById('walkthrough-overlay');
        this.spotlight = document.getElementById('walkthrough-spotlight');
        this.tooltip = document.getElementById('walkthrough-tooltip');

        const hasCompleted = localStorage.getItem('reckot_walkthrough_completed');
        const isFirstVisit = !localStorage.getItem('reckot_has_visited');

        if (isFirstVisit || !hasCompleted) {
            setTimeout(() => this.start(), 1500);
            localStorage.setItem('reckot_has_visited', 'true');
        }
    },

    start() {
        this.currentStep = 0;
        this.overlay.classList.remove('hidden');
        setTimeout(() => this.overlay.classList.add('opacity-100'), 10);
        this.createSkipButton();
        this.showStep(0);
    },

    createSkipButton() {
        this.skipButton = document.createElement('button');
        this.skipButton.className = 'fixed top-6 right-6 z-[10001] bg-white/95 hover:bg-white text-gray-600 hover:text-gray-900 px-5 py-2.5 rounded-lg shadow-lg transition-all duration-200 text-sm font-medium backdrop-blur-sm';
        this.skipButton.textContent = 'Skip Tour';
        this.skipButton.onclick = () => this.skip();
        document.body.appendChild(this.skipButton);
    },

    showStep(index) {
        if (index >= this.steps.length) {
            this.complete();
            return;
        }

        this.currentStep = index;
        const step = this.steps[index];
        const target = document.querySelector(step.target);

        if (!target) {
            console.warn(`Walkthrough target not found: ${step.target}`);
            this.next();
            return;
        }

        this.highlightElement(target);
        this.showTooltip(target, step, index);
    },

    highlightElement(element) {
        const rect = element.getBoundingClientRect();
        const padding = 12;

        this.spotlight.style.top = (rect.top + window.scrollY - padding) + 'px';
        this.spotlight.style.left = (rect.left + window.scrollX - padding) + 'px';
        this.spotlight.style.width = (rect.width + padding * 2) + 'px';
        this.spotlight.style.height = (rect.height + padding * 2) + 'px';
        this.spotlight.style.boxShadow = `0 0 0 9999px rgba(0, 0, 0, 0.75), 0 0 30px rgb(34 197 94), inset 0 0 20px rgba(34, 197, 94, 0.3)`;

        element.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
    },

    showTooltip(element, step, index) {
        const rect = element.getBoundingClientRect();
        const progress = ((index + 1) / this.steps.length) * 100;

        this.tooltip.innerHTML = `
            <div class="mb-4 flex justify-center animate-bounce">
                <i data-lucide="${step.icon}" class="w-12 h-12 ${step.iconColor}"></i>
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-3 leading-tight">${step.title}</h3>
            <p class="text-gray-600 text-sm leading-relaxed mb-6">${step.description}</p>
            <div class="flex items-center justify-between pt-5 border-t border-gray-200">
                <div class="flex items-center gap-2 text-sm font-semibold text-green-600">
                    <span>${index + 1} of ${this.steps.length}</span>
                    <div class="w-16 h-1 bg-gray-200 rounded-full overflow-hidden">
                        <div class="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-300" style="width: ${progress}%"></div>
                    </div>
                </div>
                <div class="flex gap-2">
                    ${index > 0 ? `<button class="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-semibold transition-all duration-200 inline-flex items-center gap-2" onclick="ReckotWalkthrough.previous()">
                        <i data-lucide="arrow-left" class="w-4 h-4"></i>
                        <span>Back</span>
                    </button>` : ''}
                    <button class="px-6 py-2.5 bg-gradient-to-r from-green-500 to-green-600 hover:shadow-lg hover:-translate-y-0.5 text-white rounded-lg text-sm font-semibold transition-all duration-200 inline-flex items-center gap-2" onclick="ReckotWalkthrough.next()">
                        <span>${index < this.steps.length - 1 ? 'Next' : 'Finish'}</span>
                        <i data-lucide="${index < this.steps.length - 1 ? 'arrow-right' : 'check'}" class="w-4 h-4"></i>
                    </button>
                </div>
            </div>
            ${this.getArrowHTML(step.arrow || 'up')}
        `;

        lucide.createIcons();

        setTimeout(() => {
            const tooltipRect = this.tooltip.getBoundingClientRect();
            let top, left;

            switch(step.arrow || 'up') {
                case 'up':
                    top = rect.bottom + window.scrollY + 20;
                    left = rect.left + window.scrollX + (rect.width / 2) - (tooltipRect.width / 2);
                    break;
                case 'down':
                    top = rect.top + window.scrollY - tooltipRect.height - 20;
                    left = rect.left + window.scrollX + (rect.width / 2) - (tooltipRect.width / 2);
                    break;
                case 'left':
                    top = rect.top + window.scrollY + (rect.height / 2) - (tooltipRect.height / 2);
                    left = rect.right + window.scrollX + 20;
                    break;
                case 'right':
                    top = rect.top + window.scrollY + (rect.height / 2) - (tooltipRect.height / 2);
                    left = rect.left + window.scrollX - tooltipRect.width - 20;
                    break;
            }

            top = Math.max(20, Math.min(top, window.innerHeight + window.scrollY - tooltipRect.height - 20));
            left = Math.max(20, Math.min(left, window.innerWidth - tooltipRect.width - 20));

            this.tooltip.style.top = top + 'px';
            this.tooltip.style.left = left + 'px';
            this.tooltip.classList.remove('opacity-0', 'scale-95');
            this.tooltip.classList.add('opacity-100', 'scale-100');
        }, 10);
    },

    getArrowHTML(direction) {
        const arrows = {
            up: '<div class="absolute -top-4 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[16px] border-r-[16px] border-b-[16px] border-transparent border-b-white filter drop-shadow-sm"></div>',
            down: '<div class="absolute -bottom-4 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[16px] border-r-[16px] border-t-[16px] border-transparent border-t-white filter drop-shadow-sm"></div>',
            left: '<div class="absolute -left-4 top-1/2 -translate-y-1/2 w-0 h-0 border-t-[16px] border-b-[16px] border-r-[16px] border-transparent border-r-white filter drop-shadow-sm"></div>',
            right: '<div class="absolute -right-4 top-1/2 -translate-y-1/2 w-0 h-0 border-t-[16px] border-b-[16px] border-l-[16px] border-transparent border-l-white filter drop-shadow-sm"></div>'
        };
        return arrows[direction] || arrows.up;
    },

    next() {
        this.tooltip.classList.add('opacity-0', 'scale-95');
        setTimeout(() => {
            this.showStep(this.currentStep + 1);
        }, 200);
    },

    previous() {
        if (this.currentStep > 0) {
            this.tooltip.classList.add('opacity-0', 'scale-95');
            setTimeout(() => {
                this.showStep(this.currentStep - 1);
            }, 200);
        }
    },

    skip() {
        if (confirm('Skip the tour? You can restart it anytime from Settings → Help')) {
            this.complete();
        }
    },

    complete() {
        this.tooltip.classList.add('opacity-0', 'scale-95');
        this.overlay.classList.remove('opacity-100');
        setTimeout(() => {
            this.overlay.classList.add('hidden');
            this.spotlight.classList.add('hidden');
            this.tooltip.classList.add('hidden');
            if (this.skipButton) this.skipButton.remove();
        }, 300);

        localStorage.setItem('reckot_walkthrough_completed', 'true');
        this.showCompletion();
    },

    showCompletion() {
        const completion = document.createElement('div');
        completion.innerHTML = `
            <div class="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white p-12 rounded-3xl text-center shadow-2xl z-[10001] max-w-lg opacity-0 scale-95 transition-all duration-500">
                <div class="mb-6 inline-block animate-bounce">
                    <i data-lucide="check-circle" class="w-20 h-20 text-green-500"></i>
                </div>
                <h2 class="text-4xl font-bold text-gray-900 mb-4">
                    You're Ready!
                </h2>
                <p class="text-gray-600 text-lg leading-relaxed mb-8">
                    Start creating amazing events with AI.<br>
                    Need help? Click the chat icon anytime!
                </p>
                <button onclick="this.parentElement.remove(); document.getElementById('walkthrough-overlay').remove();"
                        class="px-9 py-3.5 bg-gradient-to-r from-green-500 to-green-600 hover:shadow-xl hover:-translate-y-1 text-white rounded-xl text-lg font-semibold transition-all duration-200 inline-flex items-center gap-2">
                    <span>Start Creating Events</span>
                    <i data-lucide="arrow-right" class="w-5 h-5"></i>
                </button>
            </div>
        `;
        this.overlay.appendChild(completion);
        this.overlay.classList.remove('hidden');
        this.overlay.classList.add('opacity-100');
        this.overlay.style.background = 'rgba(0, 0, 0, 0.85)';

        setTimeout(() => {
            completion.firstElementChild.classList.remove('opacity-0', 'scale-95');
            completion.firstElementChild.classList.add('opacity-100', 'scale-100');
            lucide.createIcons();
        }, 100);
    },

    restart() {
        localStorage.removeItem('reckot_walkthrough_completed');
        location.reload();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.ReckotWalkthrough.init();
});
