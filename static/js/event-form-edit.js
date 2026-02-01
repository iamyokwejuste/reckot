document.addEventListener('DOMContentLoaded', function () {
    const aiEnabled = document.body.dataset.aiEnabled === 'true';

    if (window.AIComponents && aiEnabled) {
        setTimeout(() => {
            const descriptionField = document.querySelector('#id_description');
            if (descriptionField) {
                const wrapper = descriptionField.closest('.richtext-wrapper') || descriptionField.parentElement;
                if (wrapper) {
                    AIComponents.createDescriptionGenerator('#id_description', {
                        titleSelector: '#id_title'
                    });
                    AIComponents.createTranslateButton('#id_description', {
                        languages: ['French', 'English']
                    });
                }
            }

            const voiceCreator = AIComponents.createVoiceEventCreator();
            if (voiceCreator) {
                const progressBar = document.querySelector('.mb-8');
                if (progressBar) {
                    progressBar.parentNode.insertBefore(voiceCreator, progressBar.nextSibling);
                }
            }

            setTimeout(() => {
                AIComponents.createCoverImageGenerator();
            }, 100);
        }, 500);
    }
});
