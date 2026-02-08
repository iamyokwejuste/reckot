import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    static targets = ["dropdown", "badge", "list", "markAllBtn", "markAllBtnContainer"]

    static values = {
        open: { type: Boolean, default: false },
        unreadCount: { type: Number, default: 0 },
        loading: { type: Boolean, default: false },
        csrfToken: String,
        emptyMessage: { type: String, default: "No notifications" }
    }

    connect() {
        this.notifications = [];
        this.unreadCountValue = parseInt(this.element.dataset.unreadCount || 0);
    }

    toggle() {
        this.openValue = !this.openValue;
        if (this.openValue && this.notifications.length === 0) {
            this.fetchNotifications();
        }
    }

    close() {
        this.openValue = false;
    }

    clickOutside(event) {
        if (!this.element.contains(event.target)) {
            this.close();
        }
    }

    openValueChanged() {
        if (this.hasDropdownTarget) {
            this.dropdownTarget.classList.toggle('hidden', !this.openValue);
        }
    }

    unreadCountValueChanged() {
        if (this.hasBadgeTarget) {
            this.badgeTarget.classList.toggle('hidden', this.unreadCountValue === 0);
            this.badgeTarget.textContent = this.unreadCountValue > 99 ? '99+' : this.unreadCountValue;
        }

        if (this.hasMarkAllBtnTarget) {
            this.markAllBtnTarget.classList.toggle('hidden', this.unreadCountValue === 0);
        }

        if (this.hasMarkAllBtnContainerTarget) {
            this.markAllBtnContainerTarget.classList.toggle('hidden', this.unreadCountValue === 0);
        }
    }

    async fetchNotifications() {
        this.loadingValue = true;
        try {
            const res = await fetch('/app/api/notifications/');
            const data = await res.json();
            this.notifications = data.notifications || [];
            this.unreadCountValue = data.unread_count || 0;
            this.renderNotifications();
        } catch (e) {
            console.error('[Notifications] Failed to fetch:', e);
        }
        this.loadingValue = false;
    }

    async markAsRead(event) {
        const id = event.params.id;
        try {
            await fetch(`/app/api/notifications/${id}/read/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': this.csrfTokenValue }
            });
            const notif = this.notifications.find(n => n.id === id);
            if (notif && !notif.is_read) {
                notif.is_read = true;
                this.unreadCountValue = Math.max(0, this.unreadCountValue - 1);
                this.renderNotifications();
            }
        } catch (e) {
            console.error('[Notifications] Failed to mark as read:', e);
        }
    }

    async markAllAsRead() {
        try {
            await fetch('/app/api/notifications/read-all/', {
                method: 'POST',
                headers: { 'X-CSRFToken': this.csrfTokenValue }
            });
            this.notifications.forEach(n => n.is_read = true);
            this.unreadCountValue = 0;
            this.renderNotifications();
        } catch (e) {
            console.error('[Notifications] Failed to mark all as read:', e);
        }
    }

    renderNotifications() {
        if (!this.hasListTarget) return;

        const isMobile = this.element.id === 'mobile-notifications';

        if (this.loadingValue) {
            this.listTarget.innerHTML = isMobile ? `
                <div class="p-12 text-center text-muted-foreground">
                    <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-foreground"></div>
                </div>
            ` : `
                <div class="p-8 text-center text-muted-foreground">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-foreground"></div>
                </div>
            `;
            return;
        }

        if (this.notifications.length === 0) {
            this.listTarget.innerHTML = isMobile ? `
                <div class="p-12 text-center text-muted-foreground">
                    <i data-lucide="bell-off" class="h-16 w-16 mx-auto mb-4 opacity-50"></i>
                    <p>${this.emptyMessageValue}</p>
                </div>
            ` : `
                <div class="p-8 text-center text-muted-foreground">
                    <i data-lucide="bell-off" class="h-8 w-8 mx-auto mb-2"></i>
                    <p class="text-sm">${this.emptyMessageValue}</p>
                </div>
            `;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        this.listTarget.innerHTML = this.notifications.map(notif => {
            if (isMobile) {
                return `
                    <a href="${notif.link}"
                       data-action="click->notifications#markAsRead"
                       data-notifications-id-param="${notif.id}"
                       class="block p-4 border-b border-border active:bg-muted/80 transition-colors touch-manipulation ${notif.is_read ? 'bg-transparent' : 'bg-muted/50'}">
                        <div class="flex items-start gap-3">
                            <div class="flex-shrink-0 w-3 h-3 mt-2 rounded-full ${notif.is_read ? 'bg-transparent' : 'bg-primary'}"></div>
                            <div class="flex-1 min-w-0">
                                <p class="font-medium">${notif.title}</p>
                                <p class="text-sm text-muted-foreground line-clamp-3 mt-1">${notif.message}</p>
                                <p class="text-xs text-muted-foreground mt-2">${notif.time_ago}</p>
                            </div>
                        </div>
                    </a>
                `;
            } else {
                return `
                    <a href="${notif.link}"
                       data-action="click->notifications#markAsRead"
                       data-notifications-id-param="${notif.id}"
                       class="block p-4 border-b border-border hover:bg-muted/80 transition-colors ${notif.is_read ? 'bg-transparent' : 'bg-muted/50'}">
                        <div class="flex items-start gap-3">
                            <div class="flex-shrink-0 w-2 h-2 mt-1.5 rounded-full ${notif.is_read ? 'bg-transparent' : 'bg-primary'}"></div>
                            <div class="flex-1 min-w-0">
                                <p class="text-sm font-medium">${notif.title}</p>
                                <p class="text-xs text-muted-foreground line-clamp-2 mt-1">${notif.message}</p>
                                <p class="text-xs text-muted-foreground mt-1">${notif.time_ago}</p>
                            </div>
                        </div>
                    </a>
                `;
            }
        }).join('');

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}
