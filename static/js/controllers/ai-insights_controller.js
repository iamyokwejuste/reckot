import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["btn", "btnText", "emptyState", "loadingState", "errorState", "errorText", "resultState", "insightText"]
    static values = {
        metrics: Object,
        analyzingText: String,
        generateText: String,
        regenerateText: String,
        errorMessage: { type: String, default: "Failed to generate insight" },
        noResultMessage: { type: String, default: "No insight generated" }
    }

    connect() {
        this.generateInsight = this.generateInsight.bind(this);
    }

    showState(state) {
        this.emptyStateTarget.classList.add('hidden');
        this.loadingStateTarget.classList.add('hidden');
        this.errorStateTarget.classList.add('hidden');
        this.resultStateTarget.classList.add('hidden');
        state.classList.remove('hidden');
    }

    generateInsight() {
        this.btnTarget.disabled = true;
        this.btnTextTarget.textContent = this.analyzingTextValue;
        this.showState(this.loadingStateTarget);

        const csrfToken = this.getCSRFToken();

        fetch('/app/api/ai/insight/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ metrics: this.metricsValue })
        })
        .then(response => {
            return response.json().then(data => {
                if (!response.ok) {
                    throw new Error(data.error || this.errorMessageValue);
                }
                return data;
            });
        })
        .then(data => {
            if (data.insight) {
                this.insightTextTarget.textContent = data.insight;
                this.showState(this.resultStateTarget);
                this.btnTextTarget.textContent = this.regenerateTextValue;
            } else {
                throw new Error(this.noResultMessageValue);
            }
        })
        .catch(err => {
            this.errorTextTarget.textContent = err.message || this.errorMessageValue;
            this.showState(this.errorStateTarget);
            this.btnTextTarget.textContent = this.generateTextValue;
        })
        .finally(() => {
            this.btnTarget.disabled = false;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        });
    }

    retry() {
        this.generateInsight();
    }

    getCSRFToken() {
        let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        csrfToken = csrfToken ? csrfToken.value : '';
        if (!csrfToken) {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const c = cookies[i].trim();
                if (c.startsWith('csrftoken=')) {
                    csrfToken = c.split('=')[1];
                    break;
                }
            }
        }
        return csrfToken;
    }
}
