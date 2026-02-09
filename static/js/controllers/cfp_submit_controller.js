import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["tagInput", "tagList", "coSpeakerList", "abstractField", "abstractCount"]

    connect() {
        this.tags = [];
        this.updateAbstractCount();
    }

    addTag(event) {
        if (event.key !== "Enter") return;
        event.preventDefault();
        const value = this.tagInputTarget.value.trim();
        if (!value || this.tags.includes(value)) return;
        this.tags.push(value);
        this.renderTags();
        this.tagInputTarget.value = "";
    }

    removeTag(event) {
        const tag = event.currentTarget.dataset.tag;
        this.tags = this.tags.filter(t => t !== tag);
        this.renderTags();
    }

    renderTags() {
        this.tagListTarget.innerHTML = "";
        this.tags.forEach(tag => {
            const chip = document.createElement("span");
            chip.style.cssText = "display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background-color: #f4f4f5; border-radius: 9999px; font-size: 13px; color: #09090b;";
            chip.textContent = tag;
            const btn = document.createElement("button");
            btn.type = "button";
            btn.textContent = "\u00d7";
            btn.style.cssText = "background: none; border: none; cursor: pointer; font-size: 16px; line-height: 1; padding: 0; color: #71717a;";
            btn.dataset.tag = tag;
            btn.dataset.action = "click->cfp-submit#removeTag";
            chip.appendChild(btn);
            this.tagListTarget.appendChild(chip);
        });
        let hiddenInput = this.element.querySelector('input[name="tags"]');
        if (!hiddenInput) {
            hiddenInput = document.createElement("input");
            hiddenInput.type = "hidden";
            hiddenInput.name = "tags";
            this.element.appendChild(hiddenInput);
        }
        hiddenInput.value = JSON.stringify(this.tags);
    }

    addCoSpeaker() {
        const wrapper = document.createElement("div");
        wrapper.style.cssText = "display: flex; gap: 8px; margin-top: 8px;";
        const input = document.createElement("input");
        input.type = "email";
        input.name = "co_speaker_emails[]";
        input.placeholder = "Co-speaker email";
        input.style.cssText = "flex: 1; padding: 8px 12px; border: 1px solid #e4e4e7; border-radius: 8px; font-size: 14px;";
        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.textContent = "Remove";
        removeBtn.style.cssText = "padding: 8px 12px; background: none; border: 1px solid #e4e4e7; border-radius: 8px; font-size: 14px; cursor: pointer; color: #71717a;";
        removeBtn.addEventListener("click", () => wrapper.remove());
        wrapper.appendChild(input);
        wrapper.appendChild(removeBtn);
        this.coSpeakerListTarget.appendChild(wrapper);
    }

    removeCoSpeaker(event) {
        event.currentTarget.closest("div").remove();
    }

    updateAbstractCount() {
        if (!this.hasAbstractFieldTarget || !this.hasAbstractCountTarget) return;
        const current = this.abstractFieldTarget.value.length;
        const max = this.abstractFieldTarget.maxLength || 2000;
        this.abstractCountTarget.textContent = `${current}/${max}`;
    }

    validateAndSubmit(event) {
        const form = this.element.closest("form") || this.element;
        const requiredFields = form.querySelectorAll("[required]");
        let valid = true;
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                valid = false;
                field.style.borderColor = "#ef4444";
            } else {
                field.style.borderColor = "";
            }
        });
        if (!valid) {
            event.preventDefault();
        }
    }
}
