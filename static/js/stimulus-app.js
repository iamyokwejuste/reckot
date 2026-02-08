'use strict';

function waitForStimulus(callback) {
    if (window.Stimulus) {
        callback();
    } else {
        setTimeout(() => waitForStimulus(callback), 50);
    }
}

async function registerController(name, path) {
    try {
        const module = await import(path);
        if (!module.default) {
            return;
        }
        window.Stimulus.register(name, module.default);
    } catch (err) {}
}

waitForStimulus(async () => {
    const baseUrl = '/static/js/controllers/';
    const version = '1770504500';

    const controllers = [
        { name: 'event-form', path: 'event-form_controller.js' },
        { name: 'event-checkout', path: 'event-checkout_controller.js' },
        { name: 'discover', path: 'discover_controller.js' },
        { name: 'chatbot', path: 'chatbot_controller.js' },
        { name: 'dropdown', path: 'dropdown_controller.js' },
        { name: 'modal', path: 'modal_controller.js' },
        { name: 'toggle', path: 'toggle_controller.js' },
        { name: 'sidebar', path: 'sidebar_controller.js' },
        { name: 'tabs', path: 'tabs_controller.js' },
        { name: 'animate', path: 'animate_controller.js' },
        { name: 'accordion', path: 'accordion_controller.js' },
        { name: 'theme', path: 'theme_controller.js' },
        { name: 'navbar', path: 'navbar_controller.js' },
        { name: 'logo', path: 'logo_controller.js' },
        { name: 'login', path: 'login_controller.js' },
        { name: 'signup', path: 'signup_controller.js' },
        { name: 'notifications', path: 'notifications_controller.js' },
        { name: 'loader', path: 'loader_controller.js' },
        { name: 'clipboard', path: 'clipboard_controller.js' },
        { name: 'confirmation', path: 'confirmation_controller.js' },
        { name: 'logout', path: 'logout_controller.js' },
        { name: 'pricing-calculator', path: 'pricing-calculator_controller.js' },
        { name: 'ai-insights', path: 'ai-insights_controller.js' },
        { name: 'payment-select', path: 'payment-select_controller.js' },
        { name: 'datepicker', path: 'datepicker_controller.js' },
        { name: 'file-upload', path: 'file-upload_controller.js' },
        { name: 'file-preview', path: 'file-preview_controller.js' },
        { name: 'form-persistence', path: 'form-persistence_controller.js' },
        { name: 'motion', path: 'motion_controller.js' },
        { name: 'coupon-form', path: 'coupon-form_controller.js' },
        { name: 'checkin-offline', path: 'checkin-offline_controller.js' },
        { name: 'withdrawal', path: 'withdrawal_controller.js' },
    ];

    await Promise.all(
        controllers.map(ctrl => registerController(ctrl.name, `${baseUrl}${ctrl.path}?v=${version}`))
    );

    document.dispatchEvent(new CustomEvent('stimulus:ready'));
});

document.addEventListener('htmx:afterSwap', () => {
    if (typeof lucide !== 'undefined') {
        try {
            lucide.createIcons();
        } catch (e) {}
    }
});
