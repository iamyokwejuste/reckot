document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    if (form && window.FormPersistence) {
        const formId = 'event_create';

        const restored = FormPersistence.restore(formId, form);
        if (restored) {
            const notice = document.createElement('div');
            notice.className = 'rounded-lg bg-blue-500/10 border border-blue-500/20 p-4 text-sm text-blue-500 mb-6 flex items-center justify-between';
            notice.innerHTML = `
                <span>Draft restored from your previous session</span>
                <button type="button" onclick="FormPersistence.clear('${formId}'); this.parentElement.remove();" class="text-xs underline hover:no-underline">Dismiss</button>
            `;
            form.insertBefore(notice, form.firstChild.nextSibling);
        }

        const persistence = FormPersistence.autoSave(formId, form);

        form.addEventListener('submit', function () {
            FormPersistence.clear(formId);
            persistence.stop();
        });
    }

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
