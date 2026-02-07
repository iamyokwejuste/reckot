import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static values = {
        key: String
    }

    connect() {
        if (this.hasKeyValue && window.FormPersistence) {
            this.restore();
            this.persistence = window.FormPersistence.autoSave(this.keyValue, this.element);
            this.element.addEventListener('submit', this.handleSubmit.bind(this));
        }
    }

    disconnect() {
        if (this.persistence) {
            this.persistence.stop();
        }
        this.element.removeEventListener('submit', this.handleSubmit.bind(this));
    }

    restore() {
        window.FormPersistence.restore(this.keyValue, this.element);
    }

    handleSubmit() {
        if (this.hasKeyValue && window.FormPersistence) {
            window.FormPersistence.clear(this.keyValue);
            if (this.persistence) {
                this.persistence.stop();
            }
        }
    }
}
