document.addEventListener('alpine:init', () => {
    Alpine.data('chatbot', () => ({
        isOpen: false,
        messages: [],
        inputMessage: '',
        isLoading: false,
        sessionId: '',
        messageCounter: 0,

        init() {
            this.loadFromStorage();
            this.$nextTick(() => {
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            });
        },

        formatMessage(content) {
            if (!content) return '';

            const escapeHtml = (text) => {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            };

            let formatted = escapeHtml(content);

            formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="underline hover:text-primary" target="_blank" rel="noopener">$1</a>');
            formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
            formatted = formatted.replace(/\n/g, '<br>');
            formatted = formatted.replace(/`(.*?)`/g, '<code class="px-1 py-0.5 bg-muted rounded text-sm">$1</code>');

            formatted = formatted.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" class="underline hover:text-primary" target="_blank" rel="noopener">$1</a>');

            return formatted;
        },

        loadFromStorage() {
            try {
                const stored = localStorage.getItem('reckot_chatbot_state');
                if (stored) {
                    const state = JSON.parse(stored);
                    this.messages = state.messages || [];
                    this.sessionId = state.sessionId || '';
                    this.messageCounter = state.messageCounter || 0;
                }
                if (this.messages.length === 0) {
                    this.addWelcomeMessage();
                }
            } catch (e) {
                this.addWelcomeMessage();
            }
        },

        saveToStorage() {
            try {
                localStorage.setItem('reckot_chatbot_state', JSON.stringify({
                    messages: this.messages.slice(-50),
                    sessionId: this.sessionId,
                    messageCounter: this.messageCounter
                }));
            } catch (e) {}
        },

        toggle() {
            this.isOpen = !this.isOpen;
            if (this.isOpen && this.messages.length === 0) {
                this.addWelcomeMessage();
            }
            this.$nextTick(() => {
                this.scrollToBottom();
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            });
        },

        close() {
            this.isOpen = false;
        },

        addWelcomeMessage() {
            this.messages.push({
                id: ++this.messageCounter,
                role: 'ASSISTANT',
                content: "Hello! I'm Reckot Assistant. How can I help you today?",
                timestamp: Date.now()
            });
            this.saveToStorage();
        },

        async sendMessage(preset = null, event = null) {
            if (event) {
                event.preventDefault();
                event.stopPropagation();
            }

            const message = preset || this.inputMessage.trim();
            if (!message) return false;

            try {
                this.messages.push({
                    id: ++this.messageCounter,
                    role: 'USER',
                    content: message,
                    timestamp: Date.now()
                });
                this.inputMessage = '';
                this.isLoading = true;
                this.saveToStorage();

                this.$nextTick(() => this.scrollToBottom());

                const csrfToken = document.cookie
                    .split(';')
                    .find(c => c.trim().startsWith('csrftoken='))
                    ?.split('=')[1] || '';

                const response = await fetch('/ai/assistant/chat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: this.sessionId || null
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    this.messages.push({
                        id: ++this.messageCounter,
                        role: 'ASSISTANT',
                        content: data.error || 'Sorry, I encountered an error.',
                        timestamp: Date.now()
                    });
                } else {
                    this.messages.push({
                        id: ++this.messageCounter,
                        role: 'ASSISTANT',
                        content: data.message,
                        timestamp: Date.now()
                    });

                    if (data.session_id && !this.sessionId) {
                        this.sessionId = data.session_id;
                    }
                }
            } catch (error) {
                this.messages.push({
                    id: ++this.messageCounter,
                    role: 'ASSISTANT',
                    content: 'Sorry, something went wrong. Please try again.',
                    timestamp: Date.now()
                });
            } finally {
                this.isLoading = false;
                this.saveToStorage();
                this.$nextTick(() => this.scrollToBottom());
            }

            return false;
        },

        scrollToBottom() {
            const container = this.$refs.messages;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        },

        clearChat() {
            this.messages = [];
            this.sessionId = '';
            this.messageCounter = 0;
            localStorage.removeItem('reckot_chatbot_state');
            this.addWelcomeMessage();
        }
    }));
});
