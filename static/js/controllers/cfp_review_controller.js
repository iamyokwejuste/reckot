import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["starInput", "starDisplay", "selectAll", "proposalCheckbox", "bulkBar", "bulkCount"]

    connect() {
        this.updateBulkBar();
    }

    rate(event) {
        const value = parseInt(event.currentTarget.dataset.value, 10);
        if (!this.hasStarInputTarget) return;
        this.starInputTarget.value = value;
        this.renderStars(value);
    }

    renderStars(rating) {
        if (!this.hasStarDisplayTarget) return;
        const stars = this.starDisplayTarget.querySelectorAll("[data-star]");
        stars.forEach(star => {
            const starValue = parseInt(star.dataset.star, 10);
            if (starValue <= rating) {
                star.style.color = "#f59e0b";
            } else {
                star.style.color = "#e4e4e7";
            }
        });
    }

    toggleAll() {
        const checked = this.selectAllTarget.checked;
        this.proposalCheckboxTargets.forEach(cb => {
            cb.checked = checked;
        });
        this.updateBulkBar();
    }

    toggleOne() {
        const allChecked = this.proposalCheckboxTargets.every(cb => cb.checked);
        if (this.hasSelectAllTarget) {
            this.selectAllTarget.checked = allChecked;
        }
        this.updateBulkBar();
    }

    updateBulkBar() {
        const count = this.proposalCheckboxTargets.filter(cb => cb.checked).length;
        if (this.hasBulkBarTarget) {
            this.bulkBarTarget.classList.toggle("hidden", count === 0);
        }
        if (this.hasBulkCountTarget) {
            this.bulkCountTarget.textContent = count;
        }
    }

    filter(event) {
        event.preventDefault();
        const url = new URL(window.location.href);
        const params = event.currentTarget.dataset;
        if (params.filterKey && params.filterValue) {
            url.searchParams.set(params.filterKey, params.filterValue);
        }
        window.location.href = url.toString();
    }
}
