class CheckInOffline {
    constructor(eventSlug, orgSlug) {
        this.eventSlug = eventSlug;
        this.orgSlug = orgSlug;
        this.syncManager = null;
        this.isOfflineMode = false;
        this.statusElement = null;
        this.init();
    }

    async init() {
        if (window.offlineSync) {
            this.syncManager = window.offlineSync;
            this.setupListeners();
            await this.checkOfflineMode();
            this.updateStatusUI();
        } else {
            setTimeout(() => this.init(), 500);
        }
    }

    setupListeners() {
        this.syncManager.on('online', () => {
            console.log('[CheckIn] Online - sync available');
            this.updateStatusUI();
            this.showNotification('Back online - syncing data...', 'success');
        });

        this.syncManager.on('offline', () => {
            console.log('[CheckIn] Offline - using cached data');
            this.updateStatusUI();
            this.showNotification('Offline mode - check-ins will sync later', 'warning');
        });

        this.syncManager.on('syncCompleted', (data) => {
            console.log('[CheckIn] Sync completed:', data);
            this.updateStatusUI();
            if (data.checkins > 0 || data.swag > 0) {
                this.showNotification(
                    `Synced ${data.checkins} check-ins and ${data.swag} swag collections`,
                    'success'
                );
            }
        });

        this.syncManager.on('checkinSynced', () => {
            this.updateStatusUI();
        });

        const offlineToggle = document.getElementById('offline-mode-toggle');
        if (offlineToggle) {
            offlineToggle.addEventListener('change', (e) => {
                this.toggleOfflineMode(e.target.checked);
            });
        }

        const syncButton = document.getElementById('sync-now-btn');
        if (syncButton) {
            syncButton.addEventListener('click', () => {
                this.syncEventData();
            });
        }
    }

    async checkOfflineMode() {
        this.isOfflineMode = await this.syncManager.db.getSetting('offlineMode') || false;
        const toggle = document.getElementById('offline-mode-toggle');
        if (toggle) {
            toggle.checked = this.isOfflineMode;
        }
    }

    async toggleOfflineMode(enabled) {
        this.isOfflineMode = enabled;
        await this.syncManager.db.saveSetting('offlineMode', enabled);

        if (enabled) {
            await this.syncEventData();
            this.showNotification('Offline mode enabled - data cached', 'success');
        } else {
            this.showNotification('Offline mode disabled', 'info');
        }

        this.updateStatusUI();
    }

    async syncEventData() {
        const syncButton = document.getElementById('sync-now-btn');
        if (syncButton) {
            syncButton.disabled = true;
            syncButton.textContent = 'Syncing...';
        }

        const success = await this.syncManager.syncEventData(this.eventSlug);

        if (syncButton) {
            syncButton.disabled = false;
            syncButton.textContent = 'Sync Data';
        }

        if (success) {
            const event = await this.syncManager.db.getEventBySlug(this.eventSlug);
            const tickets = await this.syncManager.db.getEventTickets(event.id);
            this.showNotification(`Cached ${tickets.length} tickets for offline use`, 'success');
        } else {
            this.showNotification('Failed to sync event data', 'error');
        }

        this.updateStatusUI();
    }

    async updateStatusUI() {
        const status = await this.syncManager.getOfflineStatus();
        const statusBadge = document.getElementById('offline-status-badge');
        const pendingCount = document.getElementById('pending-sync-count');

        if (statusBadge) {
            const badgeClasses = [
                'inline-flex', 'items-center', 'rounded-full', 'border',
                'px-2.5', 'py-0.5', 'text-xs', 'font-semibold', 'transition-colors',
                'focus:outline-none', 'focus:ring-2', 'focus:ring-ring', 'focus:ring-offset-2'
            ];

            if (status.isOnline) {
                badgeClasses.push('border-success/20', 'bg-success/10', 'text-success');
                statusBadge.textContent = 'Online';
            } else {
                badgeClasses.push('border-warning/20', 'bg-warning/10', 'text-warning');
                statusBadge.textContent = 'Offline';
            }

            statusBadge.className = badgeClasses.join(' ');
        }

        if (pendingCount) {
            const total = status.pendingCheckins + status.pendingSwag;
            if (total > 0) {
                pendingCount.textContent = `${total} pending`;
                pendingCount.classList.remove('hidden');
            } else {
                pendingCount.classList.add('hidden');
            }
        }

        const offlineIndicator = document.getElementById('offline-mode-indicator');
        if (offlineIndicator) {
            offlineIndicator.classList.toggle('hidden', status.isOnline);
        }
    }

    async verifyTicket(code) {
        if (this.syncManager.isOnline && !this.isOfflineMode) {
            return this.verifyTicketOnline(code);
        } else {
            return this.verifyTicketOffline(code);
        }
    }

    async verifyTicketOnline(code) {
        try {
            const formData = new FormData();
            formData.append('code', code);
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch(
                `/checkin/${this.orgSlug}/${this.eventSlug}/verify/`,
                {
                    method: 'POST',
                    body: formData,
                }
            );

            const html = await response.text();
            return { success: response.ok, html };
        } catch (error) {
            console.error('[CheckIn] Online verification failed:', error);
            return this.verifyTicketOffline(code);
        }
    }

    async verifyTicketOffline(code) {
        try {
            const ticket = await this.syncManager.db.getTicketByCode(code);

            if (!ticket) {
                return {
                    success: false,
                    html: this.renderError('Ticket not found in offline cache'),
                };
            }

            if (ticket.is_checked_in || ticket.isCheckedIn) {
                return {
                    success: false,
                    html: this.renderError('Ticket already checked in'),
                };
            }

            const now = Date.now();
            const localId = await this.syncManager.db.saveCheckin({
                ticketCode: code,
                checkedInAt: now,
                notes: 'Offline check-in',
            });

            ticket.is_checked_in = true;
            ticket.isCheckedIn = true;
            ticket.checked_in_at = new Date().toISOString();
            await this.syncManager.db.updateTicket(ticket);

            const swagItems = await this.syncManager.db.getEventSwagItems(ticket.eventId);

            return {
                success: true,
                html: this.renderSuccess(ticket, swagItems, localId),
            };
        } catch (error) {
            console.error('[CheckIn] Offline verification failed:', error);
            return {
                success: false,
                html: this.renderError('Check-in failed: ' + error.message),
            };
        }
    }

    async collectSwag(checkinLocalId, swagItemId, ticketCode) {
        if (this.syncManager.isOnline && !this.isOfflineMode) {
            return this.collectSwagOnline(checkinLocalId, swagItemId);
        } else {
            return this.collectSwagOffline(checkinLocalId, swagItemId, ticketCode);
        }
    }

    async collectSwagOnline(checkinRef, swagItemId) {
        try {
            const response = await fetch(
                `/checkin/swag/${checkinRef}/${swagItemId}/`,
                {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                }
            );

            const html = await response.text();
            return { success: response.ok, html };
        } catch (error) {
            console.error('[CheckIn] Online swag collection failed:', error);
            return {
                success: false,
                html: '<div class="alert alert-error">Failed to collect swag</div>',
            };
        }
    }

    async collectSwagOffline(checkinLocalId, swagItemId, ticketCode) {
        try {
            await this.syncManager.db.saveSwagCollection({
                checkinLocalId,
                swagItemId,
                ticketCode,
                collectedAt: Date.now(),
            });

            return {
                success: true,
                html: '<div role="alert" class="relative w-full rounded-lg border p-4 border-success/50 text-success bg-success/10"><div class="text-sm leading-relaxed">Swag collected (will sync later)</div></div>',
            };
        } catch (error) {
            console.error('[CheckIn] Offline swag collection failed:', error);
            return {
                success: false,
                html: '<div role="alert" class="relative w-full rounded-lg border p-4 border-destructive/50 text-destructive bg-destructive/10"><div class="text-sm leading-relaxed">Failed to collect swag</div></div>',
            };
        }
    }

    renderSuccess(ticket, swagItems, localId) {
        const attendeeName = ticket.attendee_name || ticket.attendeeName || 'Guest';
        const ticketType = ticket.ticket_type__name || ticket['ticket_type__name'] || 'Ticket';

        let swagHtml = '';
        if (swagItems && swagItems.length > 0) {
            swagHtml = `
                <div class="mt-4">
                    <h4 class="font-semibold mb-2">Collect Swag:</h4>
                    <div class="space-y-2">
                        ${swagItems
                            .map(
                                (item) => `
                            <button
                                class="btn btn-sm btn-secondary w-full"
                                onclick="checkinOffline.collectSwag('${localId}', ${item.id}, '${ticket.code}')">
                                Collect ${item.name}
                            </button>
                        `
                            )
                            .join('')}
                    </div>
                </div>
            `;
        }

        return `
            <div role="alert" class="relative w-full rounded-lg border p-4 border-success/50 text-success bg-success/10">
                <div class="text-sm leading-relaxed">
                    <h3 class="font-bold mb-2">Check-in Successful!</h3>
                    <p>Name: ${attendeeName}</p>
                    <p>Ticket: ${ticketType}</p>
                    <p class="text-sm opacity-80 mt-2">
                        ${this.syncManager.isOnline ? 'Checked in online' : 'Offline check-in - will sync later'}
                    </p>
                    ${swagHtml}
                </div>
            </div>
        `;
    }

    renderError(message) {
        return `
            <div role="alert" class="relative w-full rounded-lg border p-4 border-destructive/50 text-destructive bg-destructive/10">
                <div class="text-sm leading-relaxed">${message}</div>
            </div>
        `;
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const variantMap = {
            info: 'default',
            success: 'success',
            warning: 'warning',
            error: 'destructive'
        };

        const variant = variantMap[type] || 'default';
        const notification = document.createElement('div');
        notification.setAttribute('role', 'alert');
        notification.className = `relative w-full rounded-lg border p-4 mb-2 ${this.getAlertClasses(variant)}`;
        notification.innerHTML = `<div class="text-sm leading-relaxed">${message}</div>`;
        container.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    getAlertClasses(variant) {
        const classes = {
            default: 'bg-background text-foreground',
            destructive: 'border-destructive/50 text-destructive bg-destructive/10',
            success: 'border-success/50 text-success bg-success/10',
            warning: 'border-warning/50 text-warning bg-warning/10'
        };
        return classes[variant] || classes.default;
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    async searchTickets(query) {
        if (!query || query.length < 2) return [];

        const event = await this.syncManager.db.getEventBySlug(this.eventSlug);
        if (!event) return [];

        const tickets = await this.syncManager.db.getEventTickets(event.id);
        const searchLower = query.toLowerCase();

        return tickets
            .filter((ticket) => {
                const code = (ticket.code || '').toLowerCase();
                const name = (ticket.attendee_name || ticket.attendeeName || '').toLowerCase();
                const email = (ticket.attendee_email || ticket.attendeeEmail || '').toLowerCase();

                return code.includes(searchLower) || name.includes(searchLower) || email.includes(searchLower);
            })
            .slice(0, 20);
    }
}

window.CheckInOffline = CheckInOffline;
window.checkinOffline = null;
