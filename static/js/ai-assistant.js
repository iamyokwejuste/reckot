const ReckotAI = {
    baseUrl: '/app/api/ai',

    async _fetch(endpoint, data) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                          document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='))?.split('=')[1];

        try {
            const response = await fetch(`${this.baseUrl}/${endpoint}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'AI request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('AI Error:', error);
            throw error;
        }
    },

    async generateDescription(context) {
        return this._fetch('generate-description', context);
    },

    async improveDescription(description) {
        return this._fetch('improve-description', { description });
    },

    async generateSEO(title, description) {
        return this._fetch('generate-seo', { title, description });
    },

    async generateCaption(title, description, platform = 'general') {
        return this._fetch('generate-caption', { title, description, platform });
    },

    async translate(text, language = 'French') {
        return this._fetch('translate', { text, language });
    },

    async summarize(text, maxWords = 30) {
        return this._fetch('summarize', { text, max_words: maxWords });
    },

    async suggestPricing(eventType, location, description) {
        return this._fetch('suggest-pricing', {
            event_type: eventType,
            location,
            description
        });
    },

    async suggestTags(title, description) {
        return this._fetch('suggest-tags', { title, description });
    },

    async askAssistant(eventInfo, question) {
        return this._fetch('assistant', { event_info: eventInfo, question });
    },

    async generateInsight(metrics) {
        return this._fetch('insight', { metrics });
    }
};


const AIComponents = {
    createButton(options = {}) {
        const {
            text = 'AI Generate',
            icon = 'sparkles',
            size = 'sm',
            variant = 'outline',
            className = ''
        } = options;

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `btn btn-${variant} btn-${size} ai-btn ${className}`.trim();
        btn.innerHTML = `
            <i data-lucide="${icon}" class="w-4 h-4"></i>
            <span>${text}</span>
            <span class="ai-loading hidden">
                <svg class="animate-spin w-4 h-4" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
            </span>
        `;

        if (typeof lucide !== 'undefined') {
            setTimeout(() => lucide.createIcons({ nodes: [btn] }), 0);
        }

        return btn;
    },

    setLoading(btn, loading) {
        const text = btn.querySelector('span:not(.ai-loading)');
        const loader = btn.querySelector('.ai-loading');
        const icon = btn.querySelector('[data-lucide]');

        if (loading) {
            btn.disabled = true;
            if (text) text.classList.add('hidden');
            if (icon) icon.classList.add('hidden');
            if (loader) loader.classList.remove('hidden');
        } else {
            btn.disabled = false;
            if (text) text.classList.remove('hidden');
            if (icon) icon.classList.remove('hidden');
            if (loader) loader.classList.add('hidden');
        }
    },

    createDescriptionGenerator(targetSelector, options = {}) {
        const target = document.querySelector(targetSelector);
        if (!target) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'ai-tools-wrapper mt-4 p-3 rounded-lg bg-muted/50 border border-border';

        const header = document.createElement('div');
        header.className = 'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3';

        const labelGroup = document.createElement('div');
        labelGroup.className = 'flex flex-col';

        const label = document.createElement('span');
        label.className = 'text-xs font-semibold text-foreground uppercase tracking-wide';
        label.textContent = 'AI Tools';

        const tagline = document.createElement('span');
        tagline.className = 'text-xs text-muted-foreground';
        tagline.textContent = 'Boost your reach with AI-powered content';

        labelGroup.appendChild(label);
        labelGroup.appendChild(tagline);
        header.appendChild(labelGroup);

        const container = document.createElement('div');
        container.className = 'flex flex-wrap items-center gap-2';

        const generateBtn = this.createButton({
            text: 'Generate',
            icon: 'sparkles',
            ...options
        });

        const improveBtn = this.createButton({
            text: 'Improve',
            icon: 'wand-2',
            ...options
        });

        container.appendChild(generateBtn);
        container.appendChild(improveBtn);
        wrapper.appendChild(header);
        wrapper.appendChild(container);

        const richtextWrapper = target.closest('.richtext-wrapper') || target.parentNode;
        richtextWrapper.parentNode.insertBefore(wrapper, richtextWrapper.nextSibling);

        generateBtn.addEventListener('click', async () => {
            const title = document.querySelector(options.titleSelector || '[name="title"]')?.value;
            if (!title) {
                this.showToast('error', 'Please enter an event title first');
                return;
            }

            this.setLoading(generateBtn, true);
            this.showPageOverlay('Generating tagline & description...');
            try {
                const context = await this.collectEventContext(options);
                const result = await ReckotAI.generateDescription(context);

                let generated = [];

                if (result.tagline) {
                    const taglineField = document.querySelector('#id_short_description, [name="short_description"]');
                    if (taglineField) {
                        taglineField.value = result.tagline;
                        taglineField.dispatchEvent(new Event('input', { bubbles: true }));
                        generated.push('tagline');
                    }
                }

                if (result.description) {
                    const desc = typeof result.description === 'object'
                        ? result.description.description || JSON.stringify(result.description)
                        : result.description;
                    this.setEditorContent(target, desc);
                    generated.push('description');
                }

                if (generated.length > 0) {
                    this.showToast('success', `Generated ${generated.join(' & ')}!`);
                }
            } catch (error) {
                this.showToast('error', error.message || 'Failed to generate');
            } finally {
                this.setLoading(generateBtn, false);
                this.hidePageOverlay();
            }
        });

        improveBtn.addEventListener('click', async () => {
            const content = this.getEditorContent(target);
            if (!content || content.length < 20) {
                this.showToast('error', 'Please write some content first');
                return;
            }

            this.setLoading(improveBtn, true);
            this.showPageOverlay('Improving description...');
            try {
                const result = await ReckotAI.improveDescription(content);
                if (result.description) {
                    this.setEditorContent(target, result.description);
                    this.showToast('success', 'Description improved!');
                }
            } catch (error) {
                this.showToast('error', error.message || 'Failed to improve');
            } finally {
                this.setLoading(improveBtn, false);
                this.hidePageOverlay();
            }
        });

        return wrapper;
    },

    collectEventContext(options = {}) {
        const context = {
            title: document.querySelector(options.titleSelector || '[name="title"]')?.value || '',
            short_description: document.querySelector('[name="short_description"]')?.value || '',
            event_type: document.querySelector('[name="event_type"]')?.value || 'general',
            location: document.querySelector('[name="location"]')?.value || ''
        };

        const coverInput = document.querySelector('[name="cover_image"]');
        if (coverInput?.files?.[0]) {
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    context.cover_image = e.target.result;
                    context.cover_image_mime = coverInput.files[0].type || 'image/jpeg';
                    resolve(context);
                };
                reader.readAsDataURL(coverInput.files[0]);
            });
        }

        const coverPreview = document.querySelector('[x-ref="coverInput"]');
        if (coverPreview?.files?.[0]) {
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    context.cover_image = e.target.result;
                    context.cover_image_mime = coverPreview.files[0].type || 'image/jpeg';
                    resolve(context);
                };
                reader.readAsDataURL(coverPreview.files[0]);
            });
        }

        return Promise.resolve(context);
    },

    showToast(type, message) {
        if (window.showToast) {
            window.showToast(type, message);
            return;
        }

        const existingToast = document.querySelector('.ai-toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = `ai-toast fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium animate-in ${
            type === 'error'
                ? 'bg-red-500/10 border border-red-500/20 text-red-500'
                : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-500'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 3000);
    },

    showPageOverlay(message = 'Generating with AI...') {
        const existing = document.getElementById('ai-page-overlay');
        if (existing) return;

        const overlay = document.createElement('div');
        overlay.id = 'ai-page-overlay';
        overlay.className = 'fixed inset-0 z-[9999] flex items-center justify-center bg-background/80 backdrop-blur-sm';
        overlay.innerHTML = `
            <div class="flex flex-col items-center gap-4 p-8 rounded-xl bg-card border border-border shadow-2xl">
                <div class="relative">
                    <div class="w-12 h-12 rounded-full border-4 border-purple-500/30 border-t-purple-500 animate-spin"></div>
                    <i data-lucide="sparkles" class="w-5 h-5 text-purple-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"></i>
                </div>
                <p class="text-sm font-medium text-foreground">${message}</p>
                <p class="text-xs text-muted-foreground">Please wait...</p>
            </div>
        `;
        document.body.appendChild(overlay);
        document.body.style.overflow = 'hidden';

        if (typeof lucide !== 'undefined') {
            lucide.createIcons({ nodes: [overlay] });
        }
    },

    hidePageOverlay() {
        const overlay = document.getElementById('ai-page-overlay');
        if (overlay) {
            overlay.remove();
            document.body.style.overflow = '';
        }
    },

    createTranslateButton(targetSelector, options = {}) {
        const target = document.querySelector(targetSelector);
        if (!target) return;

        const richtextWrapper = target.closest('.richtext-wrapper') || target.parentNode;
        const existingWrapper = richtextWrapper.parentNode.querySelector('.ai-tools-wrapper');
        const container = existingWrapper?.querySelector('.flex.flex-wrap') || null;

        if (container) {
            const separator = document.createElement('div');
            separator.className = 'hidden sm:block w-px h-6 bg-border mx-1';
            container.appendChild(separator);
        }

        const languages = options.languages || ['French', 'English'];

        languages.forEach(lang => {
            const btn = this.createButton({
                text: lang,
                icon: 'languages',
                size: 'sm',
                variant: 'ghost'
            });

            btn.addEventListener('click', async () => {
                const content = this.getEditorContent(target);
                if (!content) {
                    this.showToast('error', 'No content to translate');
                    return;
                }

                this.setLoading(btn, true);
                this.showPageOverlay(`Translating to ${lang}...`);
                try {
                    const result = await ReckotAI.translate(content, lang);
                    if (result.translation) {
                        this.setEditorContent(target, result.translation);
                        this.showToast('success', `Translated to ${lang}!`);
                    }
                } catch (error) {
                    this.showToast('error', error.message || 'Failed to translate');
                } finally {
                    this.setLoading(btn, false);
                    this.hidePageOverlay();
                }
            });

            if (container) {
                container.appendChild(btn);
            }
        });

        return existingWrapper;
    },

    createSocialCaptionGenerator(options = {}) {
        const container = document.createElement('div');
        container.className = 'ai-social-generator card p-4';
        container.innerHTML = `
            <h4 class="font-medium mb-3 flex items-center gap-2">
                <i data-lucide="share-2" class="w-4 h-4"></i>
                Generate Social Captions
            </h4>
            <div class="grid grid-cols-2 gap-2 mb-3">
                <button type="button" data-platform="twitter" class="btn btn-outline btn-sm">
                    <i data-lucide="twitter" class="w-4 h-4"></i> Twitter
                </button>
                <button type="button" data-platform="facebook" class="btn btn-outline btn-sm">
                    <i data-lucide="facebook" class="w-4 h-4"></i> Facebook
                </button>
                <button type="button" data-platform="instagram" class="btn btn-outline btn-sm">
                    <i data-lucide="instagram" class="w-4 h-4"></i> Instagram
                </button>
                <button type="button" data-platform="linkedin" class="btn btn-outline btn-sm">
                    <i data-lucide="linkedin" class="w-4 h-4"></i> LinkedIn
                </button>
            </div>
            <div class="ai-caption-output hidden">
                <textarea class="input w-full" rows="4" readonly></textarea>
                <button type="button" class="btn btn-sm btn-ghost mt-2 copy-btn">
                    <i data-lucide="copy" class="w-4 h-4"></i> Copy
                </button>
            </div>
        `;

        if (typeof lucide !== 'undefined') {
            setTimeout(() => lucide.createIcons({ nodes: [container] }), 0);
        }

        const output = container.querySelector('.ai-caption-output');
        const textarea = container.querySelector('textarea');
        const copyBtn = container.querySelector('.copy-btn');

        container.querySelectorAll('[data-platform]').forEach(btn => {
            btn.addEventListener('click', async () => {
                const platform = btn.dataset.platform;
                const title = document.querySelector(options.titleSelector || '[name="title"]')?.value;
                const description = options.getDescription?.() || document.querySelector('[name="description"]')?.value;

                if (!title) {
                    AIComponents.showToast('error', 'Please enter an event title');
                    return;
                }

                btn.disabled = true;
                btn.innerHTML = '<svg class="animate-spin w-4 h-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>';

                try {
                    const result = await ReckotAI.generateCaption(title, description, platform);
                    if (result.caption) {
                        textarea.value = result.caption;
                        output.classList.remove('hidden');
                    }
                } catch (error) {
                    AIComponents.showToast('error', error.message || 'Failed to generate caption');
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = `<i data-lucide="${platform}" class="w-4 h-4"></i> ${platform.charAt(0).toUpperCase() + platform.slice(1)}`;
                    if (typeof lucide !== 'undefined') lucide.createIcons({ nodes: [btn] });
                }
            });
        });

        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(textarea.value);
            AIComponents.showToast('success', 'Copied to clipboard!');
        });

        return container;
    },

    createPricingSuggester(options = {}) {
        const btn = this.createButton({
            text: 'Suggest Pricing',
            icon: 'sparkles',
            ...options
        });

        btn.addEventListener('click', async () => {
            const eventType = document.querySelector(options.eventTypeSelector || '[name="event_type"]')?.value || 'general';
            const location = document.querySelector(options.locationSelector || '[name="location"]')?.value || 'Cameroon';
            const description = options.getDescription?.() || document.querySelector('[name="description"]')?.value || '';

            this.setLoading(btn, true);
            try {
                const result = await ReckotAI.suggestPricing(eventType, location, description);
                if (result.early_bird !== undefined) {
                    const message = `
Suggested Pricing (XAF):
• Early Bird: ${result.early_bird?.toLocaleString() || 'N/A'}
• Regular: ${result.regular?.toLocaleString() || 'N/A'}
• VIP: ${result.vip?.toLocaleString() || 'N/A'}

${result.reasoning || ''}
                    `.trim();
                    alert(message);
                }
            } catch (error) {
                AIComponents.showToast('error', error.message || 'Failed to suggest pricing');
            } finally {
                this.setLoading(btn, false);
            }
        });

        return btn;
    },

    createEventAssistant(eventInfo, containerSelector) {
        const container = document.querySelector(containerSelector);
        if (!container) return;

        container.innerHTML = `
            <div class="ai-assistant card p-4">
                <h4 class="font-medium mb-3 flex items-center gap-2">
                    <i data-lucide="bot" class="w-5 h-5"></i>
                    Event Assistant
                </h4>
                <div class="ai-messages space-y-3 max-h-64 overflow-y-auto mb-3"></div>
                <form class="flex gap-2">
                    <input type="text" class="input flex-1" placeholder="Ask about this event..." required>
                    <button type="submit" class="btn btn-primary btn-sm">
                        <i data-lucide="send" class="w-4 h-4"></i>
                    </button>
                </form>
            </div>
        `;

        if (typeof lucide !== 'undefined') {
            setTimeout(() => lucide.createIcons({ nodes: [container] }), 0);
        }

        const messages = container.querySelector('.ai-messages');
        const form = container.querySelector('form');
        const input = container.querySelector('input');
        const submitBtn = container.querySelector('button[type="submit"]');

        const addMessage = (text, isUser = false) => {
            const msg = document.createElement('div');
            msg.className = `p-3 rounded-lg text-sm ${isUser ? 'bg-primary/10 ml-8' : 'bg-muted mr-8'}`;
            msg.textContent = text;
            messages.appendChild(msg);
            messages.scrollTop = messages.scrollHeight;
        };

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const question = input.value.trim();
            if (!question) return;

            addMessage(question, true);
            input.value = '';
            submitBtn.disabled = true;

            try {
                const result = await ReckotAI.askAssistant(eventInfo, question);
                if (result.answer) {
                    addMessage(result.answer);
                }
            } catch (error) {
                addMessage('Sorry, I could not process that question.');
            } finally {
                submitBtn.disabled = false;
            }
        });

        return container;
    },

    getEditorContent(element) {
        const wrapper = element.closest('.richtext-wrapper') || element.parentElement;
        const editor = wrapper?.querySelector('.richtext-editor');
        if (editor) {
            return editor.innerText || editor.textContent;
        }
        return element.value;
    },

    setEditorContent(element, content) {
        const wrapper = element.closest('.richtext-wrapper') || element.parentElement;
        const editor = wrapper?.querySelector('.richtext-editor');

        const htmlContent = content.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
        const formatted = `<p>${htmlContent}</p>`;

        if (editor) {
            editor.innerHTML = formatted;
            element.value = formatted;
            element.dispatchEvent(new Event('input', { bubbles: true }));
        } else {
            element.value = content;
            element.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
};

window.ReckotAI = ReckotAI;
window.AIComponents = AIComponents;
