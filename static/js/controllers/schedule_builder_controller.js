import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["session", "slot", "sidebar", "grid"]
    static values = {
        updateUrl: String,
        csrfToken: String
    }

    connect() {
        this.sessionTargets.forEach(session => {
            session.draggable = true;
            session.addEventListener("dragstart", this.dragStart.bind(this));
            session.addEventListener("dragend", this.dragEnd.bind(this));
        });
        this.slotTargets.forEach(slot => {
            slot.addEventListener("dragover", this.dragOver.bind(this));
            slot.addEventListener("dragleave", this.dragLeave.bind(this));
            slot.addEventListener("drop", this.drop.bind(this));
        });
    }

    dragStart(event) {
        event.dataTransfer.setData("text/plain", event.currentTarget.dataset.sessionId);
        event.dataTransfer.effectAllowed = "move";
        event.currentTarget.style.opacity = "0.5";
        this.slotTargets.forEach(slot => {
            slot.style.outline = "2px dashed #a1a1aa";
            slot.style.outlineOffset = "-2px";
        });
    }

    dragEnd(event) {
        event.currentTarget.style.opacity = "1";
        this.slotTargets.forEach(slot => {
            slot.style.outline = "";
            slot.style.outlineOffset = "";
            slot.style.backgroundColor = "";
        });
    }

    dragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        event.currentTarget.style.backgroundColor = "#f4f4f5";
    }

    dragLeave(event) {
        event.currentTarget.style.backgroundColor = "";
    }

    drop(event) {
        event.preventDefault();
        const sessionId = event.dataTransfer.getData("text/plain");
        const slot = event.currentTarget;
        const startsAt = slot.dataset.startsAt;
        const endsAt = slot.dataset.endsAt;
        const trackId = slot.dataset.trackId;

        slot.style.backgroundColor = "";

        fetch(this.updateUrlValue, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": this.csrfTokenValue
            },
            body: JSON.stringify({
                session_id: sessionId,
                starts_at: startsAt,
                ends_at: endsAt,
                track_id: trackId
            })
        }).then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error("Failed to update session");
        }).then(() => {
            const session = this.sessionTargets.find(s => s.dataset.sessionId === sessionId);
            if (session) {
                slot.appendChild(session);
            }
        }).catch(() => {});
    }
}
