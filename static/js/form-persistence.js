if (!window.FormPersistence) {
    window.FormPersistence = {
        PREFIX: 'reckot_form_',

        save(formId, data) {
            const key = this.PREFIX + formId;
            localStorage.setItem(key, JSON.stringify({
                data,
                timestamp: Date.now()
            }));
        },

        load(formId) {
            const key = this.PREFIX + formId;
            const stored = localStorage.getItem(key);
            if (!stored) return null;

            try {
                const parsed = JSON.parse(stored);
                const hourAgo = Date.now() - (60 * 60 * 1000);
                if (parsed.timestamp < hourAgo) {
                    this.clear(formId);
                    return null;
                }
                return parsed.data;
            } catch {
                return null;
            }
        },

        clear(formId) {
            const key = this.PREFIX + formId;
            localStorage.removeItem(key);
        },

        autoSave(formId, form, interval = 2000) {
            let timeout;

            const save = () => {
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    if (key !== 'csrfmiddlewaretoken') {
                        data[key] = value;
                    }
                });
                this.save(formId, data);
            };

            const debouncedSave = () => {
                clearTimeout(timeout);
                timeout = setTimeout(save, interval);
            };

            form.addEventListener('input', debouncedSave);
            form.addEventListener('change', debouncedSave);

            return {
                stop: () => {
                    form.removeEventListener('input', debouncedSave);
                    form.removeEventListener('change', debouncedSave);
                    clearTimeout(timeout);
                },
                saveNow: save
            };
        },

        restore(formId, form) {
            const data = this.load(formId);
            if (!data) return false;

            Object.entries(data).forEach(([key, value]) => {
                const field = form.elements[key];
                if (field) {
                    if (field.type === 'checkbox') {
                        field.checked = value === 'on' || value === true;
                    } else if (field.type === 'file') {
                    } else {
                        field.value = value;
                    }
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });

            return true;
        }
    };
}
