import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["container", "messages", "input", "sendButton", "voiceButton"]

    static values = {
        isOpen: { type: Boolean, default: false },
        isLoading: { type: Boolean, default: false },
        isListening: { type: Boolean, default: false }
    }

    connect() {
        this.messages = [];
        this.sessionId = '';
        this.messageCounter = 0;
        this.mediaRecorder = null;
        this.audioChunks = [];

        this.loadFromStorage();
        this.initLucide();
        this.updateSendButton();
    }

    updateSendButton() {
        if (this.hasInputTarget && this.hasSendButtonTarget) {
            const hasText = this.inputTarget.value.trim().length > 0;
            this.sendButtonTarget.disabled = !hasText || this.isLoadingValue || this.isListeningValue;
        }
    }

    disconnect() {
        this.stopRecording();
    }

    isOpenValueChanged(isOpen) {
        if (this.hasContainerTarget) {
            this.containerTarget.classList.toggle('hidden', !isOpen);
            if (isOpen) {
                this.containerTarget.classList.add('chatbot-open');
            } else {
                this.containerTarget.classList.remove('chatbot-open');
            }
        }

        const trigger = this.element.querySelector('[data-chatbot-trigger]');
        if (trigger) {
            trigger.classList.toggle('hidden', isOpen);
        }

        if (isOpen) {
            this.scrollToBottom();
            if (this.hasInputTarget) {
                this.inputTarget.focus();
            }
        }
    }

    isLoadingValueChanged(isLoading) {
        if (this.hasInputTarget) {
            this.inputTarget.disabled = isLoading || this.isListeningValue;
        }
        if (this.hasVoiceButtonTarget) {
            this.voiceButtonTarget.disabled = isLoading;
        }
        this.updateSendButton();
    }

    isListeningValueChanged(isListening) {
        if (this.hasVoiceButtonTarget) {
            const icon = this.voiceButtonTarget.querySelector('[data-lucide]');
            if (icon) {
                icon.setAttribute('data-lucide', isListening ? 'mic-off' : 'mic');
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }

            if (isListening) {
                this.voiceButtonTarget.classList.add('bg-red-500', 'text-white', 'shadow-lg');
                this.voiceButtonTarget.classList.remove('bg-muted', 'hover:bg-muted/80', 'text-foreground');
            } else {
                this.voiceButtonTarget.classList.remove('bg-red-500', 'text-white', 'shadow-lg');
                this.voiceButtonTarget.classList.add('bg-muted', 'hover:bg-muted/80', 'text-foreground');
            }
        }

        if (this.hasInputTarget) {
            this.inputTarget.disabled = this.isLoadingValue || isListening;
        }

        this.updateSendButton();
    }

    toggle() {
        this.isOpenValue = !this.isOpenValue;
        if (this.isOpenValue && this.messages.length === 0) {
            this.addWelcomeMessage();
        }
        this.initLucide();
    }

    close() {
        this.isOpenValue = false;
    }

    handleEnter(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            event.stopPropagation();
            this.sendMessage();
        }
    }

    async sendMessage(event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        if (!this.hasInputTarget) return;
        const message = this.inputTarget.value.trim();
        if (!message) return;

        this.addMessage('USER', message);
        this.inputTarget.value = '';
        this.updateSendButton();
        this.isLoadingValue = true;

        this.showTypingIndicator();

        try {
            const response = await fetch('/ai/assistant/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId || null
                })
            });

            const data = await response.json();

            this.hideTypingIndicator();

            if (response.ok) {
                await this.typeMessage('ASSISTANT', data.message);
                if (data.session_id && !this.sessionId) {
                    this.sessionId = data.session_id;
                }
            } else {
                await this.typeMessage('ASSISTANT', data.error || 'Sorry, I encountered an error.');
            }
        } catch (error) {
            this.hideTypingIndicator();
            await this.typeMessage('ASSISTANT', 'Sorry, something went wrong. Please try again.');
        } finally {
            this.isLoadingValue = false;
            this.saveToStorage();
        }
    }

    showTypingIndicator() {
        if (!this.hasMessagesTarget) return;

        const typingHtml = `
            <div class="message message-assistant typing-indicator flex justify-start mb-3">
                <div class="flex items-start gap-2 max-w-[85%]">
                    <div class="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 flex-shrink-0">
                        <i data-lucide="bot" class="w-4 h-4 text-primary"></i>
                    </div>
                    <div class="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                        <div class="flex gap-1 items-center">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.messagesTarget.insertAdjacentHTML('beforeend', typingHtml);
        this.scrollToBottom();
        this.initLucide();
    }

    hideTypingIndicator() {
        if (!this.hasMessagesTarget) return;
        const typingIndicator = this.messagesTarget.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async typeMessage(role, content) {
        const messageId = ++this.messageCounter;
        const message = {
            id: messageId,
            role: role,
            content: '',
            timestamp: Date.now()
        };

        this.messages.push(message);
        this.renderMessages();

        const words = content.split(' ');
        for (let i = 0; i < words.length; i++) {
            message.content += (i > 0 ? ' ' : '') + words[i];
            this.updateMessageContent(messageId, message.content);
            await new Promise(resolve => setTimeout(resolve, 30));
        }

        this.saveToStorage();
    }

    updateMessageContent(messageId, content) {
        const messageElements = this.messagesTarget.querySelectorAll('.message');
        const messageElement = Array.from(messageElements).find(el => {
            return el.dataset.messageId == messageId;
        });

        if (messageElement) {
            const contentElement = messageElement.querySelector('.message-content');
            if (contentElement) {
                contentElement.innerHTML = this.formatMessage(content);
            }
        }
    }

    async toggleVoiceInput() {
        if (this.isListeningValue) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                stream.getTracks().forEach(track => track.stop());
                this.processRecording();
            };

            this.mediaRecorder.start();
            this.isListeningValue = true;
        } catch (error) {
            this.addMessage('ASSISTANT', 'Microphone access denied. Please allow microphone access and try again.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        this.isListeningValue = false;
    }

    async processRecording() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = async () => {
            const base64Audio = reader.result.split(',')[1];
            await this.transcribeAudio(base64Audio, 'audio/webm');
        };
    }

    async transcribeAudio(base64Audio, mimeType) {
        this.isLoadingValue = true;

        try {
            const response = await fetch('/ai/assistant/transcribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    audio: base64Audio,
                    mimeType: mimeType
                })
            });

            const data = await response.json();

            if (response.ok && data.transcription && this.hasInputTarget) {
                this.inputTarget.value = data.transcription;
                await this.sendMessage();
            } else {
                this.addMessage('ASSISTANT', 'Could not transcribe audio. Please try again.');
            }
        } catch (error) {
            this.addMessage('ASSISTANT', 'Transcription failed. Please try again.');
        } finally {
            this.isLoadingValue = false;
        }
    }

    async clearChat() {
        if (this.sessionId) {
            try {
                await fetch('/ai/assistant/clear/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify({ session_id: this.sessionId })
                });
            } catch (error) {}
        }

        this.messages = [];
        this.sessionId = '';
        this.messageCounter = 0;
        localStorage.removeItem('reckot_chatbot_state');
        this.addWelcomeMessage();
        this.renderMessages();
    }

    addMessage(role, content) {
        this.messages.push({
            id: ++this.messageCounter,
            role: role,
            content: content,
            timestamp: Date.now()
        });
        this.renderMessages();
        this.saveToStorage();
    }

    addWelcomeMessage() {
        this.addMessage('ASSISTANT', "Hello! I'm Reckot Assistant. How can I help you today?");
    }

    renderMessages() {
        if (!this.hasMessagesTarget) return;

        this.messagesTarget.innerHTML = this.messages.map(msg => {
            if (msg.role === 'USER') {
                return `
                    <div class="message message-user flex justify-end mb-3" data-message-id="${msg.id}">
                        <div class="flex items-start gap-2 max-w-[85%]">
                            <div class="message-content bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-2.5 shadow-sm">
                                ${this.formatMessage(msg.content)}
                            </div>
                            <div class="flex items-center justify-center w-8 h-8 rounded-full bg-primary flex-shrink-0">
                                <i data-lucide="user" class="w-4 h-4 text-primary-foreground"></i>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                return `
                    <div class="message message-assistant flex justify-start mb-3" data-message-id="${msg.id}">
                        <div class="flex items-start gap-2 max-w-[85%]">
                            <div class="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 flex-shrink-0">
                                <i data-lucide="bot" class="w-4 h-4 text-primary"></i>
                            </div>
                            <div class="message-content bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-2.5 shadow-sm">
                                ${this.formatMessage(msg.content)}
                            </div>
                        </div>
                    </div>
                `;
            }
        }).join('');

        this.scrollToBottom();
        this.initLucide();
    }

    formatMessage(content) {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    }

    scrollToBottom() {
        if (this.hasMessagesTarget) {
            this.messagesTarget.scrollTop = this.messagesTarget.scrollHeight;
        }
    }

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
            } else {
                this.renderMessages();
            }
        } catch (e) {
            this.addWelcomeMessage();
        }
    }

    saveToStorage() {
        try {
            localStorage.setItem('reckot_chatbot_state', JSON.stringify({
                messages: this.messages.slice(-50),
                sessionId: this.sessionId,
                messageCounter: this.messageCounter
            }));
        } catch (e) {}
    }

    getCsrfToken() {
        return document.cookie
            .split(';')
            .find(c => c.trim().startsWith('csrftoken='))
            ?.split('=')[1] || '';
    }

    initLucide() {
        requestAnimationFrame(() => {
            if (typeof lucide !== 'undefined') {
                try {
                    lucide.createIcons();
                } catch (e) {}
            }
        });
    }
}
