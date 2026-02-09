'use strict';

window.FlyerGeneratorUtils = {
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    previewPhoto(file) {
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                document.getElementById('photo-image').src = e.target.result;
                document.getElementById('photo-placeholder').classList.add('hidden');
                document.getElementById('photo-preview').classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }
    },

    showGenerationError(message) {
        const errorDiv = document.getElementById('generation-error');
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    },

    hideGenerationError() {
        const errorDiv = document.getElementById('generation-error');
        errorDiv.classList.add('hidden');
    },

    async shareFlyer(imgSrc, eventSlug, title, text) {
        const img = document.getElementById('flyer-result');
        if (navigator.share) {
            try {
                const response = await fetch(img.src);
                const blob = await response.blob();
                const file = new File([blob], `${eventSlug}-flyer.jpg`, { type: 'image/jpeg' });
                await navigator.share({
                    files: [file],
                    title: title,
                    text: text
                });
            } catch (error) { }
        } else {
            alert(window.FlyerGeneratorTranslations?.sharNotSupported || 'Sharing is not supported on your device. Please use the download button.');
        }
    }
};

// Expose individual functions globally for backward compatibility
window.getCookie = window.FlyerGeneratorUtils.getCookie;
window.previewPhoto = window.FlyerGeneratorUtils.previewPhoto;
window.showGenerationError = window.FlyerGeneratorUtils.showGenerationError;
window.hideGenerationError = window.FlyerGeneratorUtils.hideGenerationError;
window.shareFlyer = function () {
    const eventSlug = document.querySelector('[data-event-slug]')?.dataset.eventSlug || 'event';
    const title = document.querySelector('[data-share-title]')?.dataset.shareTitle || 'My Event Flyer';
    const text = document.querySelector('[data-share-text]')?.dataset.shareText || 'Check out my flyer!';
    return window.FlyerGeneratorUtils.shareFlyer(null, eventSlug, title, text);
};
