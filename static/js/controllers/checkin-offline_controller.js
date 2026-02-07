import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static values = {
        eventSlug: String,
        orgSlug: String
    }

    connect() {
        this.initializeOfflineCheckin();
        this.registerServiceWorker();
    }

    initializeOfflineCheckin() {
        if (window.CheckInOffline && this.hasEventSlugValue && this.hasOrgSlugValue) {
            window.checkinOffline = new window.CheckInOffline(this.eventSlugValue, this.orgSlugValue);
        }
    }

    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js')
                .then((registration) => {
                    console.log('[ServiceWorker] Registered:', registration);
                })
                .catch((error) => {
                    console.error('[ServiceWorker] Registration failed:', error);
                });
        }
    }
}
