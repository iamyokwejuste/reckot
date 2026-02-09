'use strict';

document.addEventListener('stimulus:ready', function () {
    document.body.setAttribute('data-controller', 'theme');
});

document.addEventListener('DOMContentLoaded', function () {
    const logoLightUrl = '/static/images/logo/reckto_logo_light_mode.png';
    const logoDarkUrl = '/static/images/logo/reckto_logo_dark_mode.png';

    const mode = localStorage.getItem('theme') || 'system';
    const isDark = mode === 'dark' || (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    const logoUrl = isDark ? logoDarkUrl : logoLightUrl;
    const spinnerColor = isDark ? '#fafafa' : '#09090b';

    const loader = document.createElement('div');
    loader.id = 'page-loader';
    loader.className = 'fixed inset-0 z-[9999] flex items-center justify-center transition-opacity duration-300';
    loader.setAttribute('hx-preserve', 'true');
    loader.style.backgroundColor = isDark ? '#09090b' : '#fafafa';
    loader.innerHTML = `
        <div class="relative w-40 h-40">
            <div class="absolute inset-0 animate-spin rounded-full" style="border: 4px solid rgba(0,0,0,0.1); border-top-color: ${spinnerColor}; color: ${spinnerColor};"></div>
            <div class="absolute inset-0 flex items-center justify-center">
                <img src="${logoUrl}" alt="Reckot" class="h-24 w-24 object-contain" loading="eager">
            </div>
        </div>
    `;
    document.body.insertBefore(loader, document.body.firstChild);

    function hideLoader() {
        loader.style.opacity = '0';
        setTimeout(() => loader.style.display = 'none', 300);
    }

    if (document.readyState === 'complete') {
        setTimeout(hideLoader, 800);
    } else {
        window.addEventListener('load', () => {
            setTimeout(hideLoader, 800);
        });
    }
});
