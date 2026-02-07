class OfflineDB {
    constructor() {
        this.dbName = 'reckot_offline';
        this.version = 1;
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                if (!db.objectStoreNames.contains('events')) {
                    const eventsStore = db.createObjectStore('events', { keyPath: 'id' });
                    eventsStore.createIndex('slug', 'slug', { unique: true });
                    eventsStore.createIndex('syncedAt', 'syncedAt', { unique: false });
                }

                if (!db.objectStoreNames.contains('tickets')) {
                    const ticketsStore = db.createObjectStore('tickets', { keyPath: 'id' });
                    ticketsStore.createIndex('code', 'code', { unique: true });
                    ticketsStore.createIndex('eventId', 'eventId', { unique: false });
                    ticketsStore.createIndex('isCheckedIn', 'isCheckedIn', { unique: false });
                }

                if (!db.objectStoreNames.contains('checkins')) {
                    const checkinsStore = db.createObjectStore('checkins', { keyPath: 'localId', autoIncrement: true });
                    checkinsStore.createIndex('ticketCode', 'ticketCode', { unique: false });
                    checkinsStore.createIndex('synced', 'synced', { unique: false });
                    checkinsStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                if (!db.objectStoreNames.contains('swagItems')) {
                    const swagStore = db.createObjectStore('swagItems', { keyPath: 'id' });
                    swagStore.createIndex('eventId', 'eventId', { unique: false });
                }

                if (!db.objectStoreNames.contains('swagCollections')) {
                    const collectionsStore = db.createObjectStore('swagCollections', { keyPath: 'localId', autoIncrement: true });
                    collectionsStore.createIndex('checkinLocalId', 'checkinLocalId', { unique: false });
                    collectionsStore.createIndex('synced', 'synced', { unique: false });
                }

                if (!db.objectStoreNames.contains('settings')) {
                    db.createObjectStore('settings', { keyPath: 'key' });
                }
            };
        });
    }

    async getStore(storeName, mode = 'readonly') {
        if (!this.db) await this.init();
        const transaction = this.db.transaction(storeName, mode);
        return transaction.objectStore(storeName);
    }

    async saveEvent(eventData) {
        const store = await this.getStore('events', 'readwrite');
        eventData.syncedAt = Date.now();
        return new Promise((resolve, reject) => {
            const request = store.put(eventData);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getEvent(eventId) {
        const store = await this.getStore('events');
        return new Promise((resolve, reject) => {
            const request = store.get(eventId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getEventBySlug(slug) {
        const store = await this.getStore('events');
        const index = store.index('slug');
        return new Promise((resolve, reject) => {
            const request = index.get(slug);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async saveTickets(tickets) {
        const store = await this.getStore('tickets', 'readwrite');
        const promises = tickets.map(ticket => {
            return new Promise((resolve, reject) => {
                const request = store.put(ticket);
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        });
        return Promise.all(promises);
    }

    async getTicketByCode(code) {
        const store = await this.getStore('tickets');
        const index = store.index('code');
        return new Promise((resolve, reject) => {
            const request = index.get(code);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getEventTickets(eventId) {
        const store = await this.getStore('tickets');
        const index = store.index('eventId');
        return new Promise((resolve, reject) => {
            const request = index.getAll(eventId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateTicket(ticket) {
        const store = await this.getStore('tickets', 'readwrite');
        return new Promise((resolve, reject) => {
            const request = store.put(ticket);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async saveCheckin(checkinData) {
        const store = await this.getStore('checkins', 'readwrite');
        checkinData.synced = false;
        checkinData.timestamp = Date.now();
        return new Promise((resolve, reject) => {
            const request = store.add(checkinData);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getUnsyncedCheckins() {
        const store = await this.getStore('checkins');
        const index = store.index('synced');
        return new Promise((resolve, reject) => {
            const request = index.getAll(false);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async markCheckinSynced(localId, serverReference) {
        const store = await this.getStore('checkins', 'readwrite');
        return new Promise((resolve, reject) => {
            const getRequest = store.get(localId);
            getRequest.onsuccess = () => {
                const checkin = getRequest.result;
                if (checkin) {
                    checkin.synced = true;
                    checkin.serverReference = serverReference;
                    const putRequest = store.put(checkin);
                    putRequest.onsuccess = () => resolve(putRequest.result);
                    putRequest.onerror = () => reject(putRequest.error);
                } else {
                    reject(new Error('Checkin not found'));
                }
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    async saveSwagItems(swagItems) {
        const store = await this.getStore('swagItems', 'readwrite');
        const promises = swagItems.map(item => {
            return new Promise((resolve, reject) => {
                const request = store.put(item);
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        });
        return Promise.all(promises);
    }

    async getEventSwagItems(eventId) {
        const store = await this.getStore('swagItems');
        const index = store.index('eventId');
        return new Promise((resolve, reject) => {
            const request = index.getAll(eventId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async saveSwagCollection(collectionData) {
        const store = await this.getStore('swagCollections', 'readwrite');
        collectionData.synced = false;
        collectionData.timestamp = Date.now();
        return new Promise((resolve, reject) => {
            const request = store.add(collectionData);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getUnsyncedSwagCollections() {
        const store = await this.getStore('swagCollections');
        const index = store.index('synced');
        return new Promise((resolve, reject) => {
            const request = index.getAll(false);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async markSwagCollectionSynced(localId) {
        const store = await this.getStore('swagCollections', 'readwrite');
        return new Promise((resolve, reject) => {
            const getRequest = store.get(localId);
            getRequest.onsuccess = () => {
                const collection = getRequest.result;
                if (collection) {
                    collection.synced = true;
                    const putRequest = store.put(collection);
                    putRequest.onsuccess = () => resolve(putRequest.result);
                    putRequest.onerror = () => reject(putRequest.error);
                } else {
                    reject(new Error('Swag collection not found'));
                }
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    async saveSetting(key, value) {
        const store = await this.getStore('settings', 'readwrite');
        return new Promise((resolve, reject) => {
            const request = store.put({ key, value });
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getSetting(key) {
        const store = await this.getStore('settings');
        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result?.value);
            request.onerror = () => reject(request.error);
        });
    }

    async clearEventData(eventId) {
        const ticketsStore = await this.getStore('tickets', 'readwrite');
        const ticketsIndex = ticketsStore.index('eventId');
        const ticketsRequest = ticketsIndex.getAllKeys(eventId);

        ticketsRequest.onsuccess = () => {
            const keys = ticketsRequest.result;
            keys.forEach(key => ticketsStore.delete(key));
        };

        const eventsStore = await this.getStore('events', 'readwrite');
        eventsStore.delete(eventId);
    }
}

class OfflineSyncManager {
    constructor() {
        this.db = new OfflineDB();
        this.syncInterval = 5 * 60 * 1000;
        this.syncTimer = null;
        this.isOnline = navigator.onLine;
        this.isSyncing = false;
        this.eventListeners = new Map();
    }

    async init() {
        await this.db.init();
        this.setupNetworkListeners();
        this.startPeriodicSync();
        return this;
    }

    setupNetworkListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.emit('online');
            this.syncNow();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.emit('offline');
        });

        setInterval(async () => {
            const wasOnline = this.isOnline;
            const isOnline = await this.checkConnectivity();
            if (isOnline !== wasOnline) {
                this.isOnline = isOnline;
                this.emit(isOnline ? 'online' : 'offline');
                if (isOnline) this.syncNow();
            }
        }, 10000);
    }

    async checkConnectivity() {
        if (!navigator.onLine) return false;
        try {
            const response = await fetch('/health/', {
                method: 'HEAD',
                cache: 'no-cache'
            });
            return response.ok;
        } catch {
            return false;
        }
    }

    startPeriodicSync() {
        if (this.syncTimer) clearInterval(this.syncTimer);
        this.syncTimer = setInterval(() => {
            if (this.isOnline) this.syncNow();
        }, this.syncInterval);
    }

    async syncEventData(eventSlug) {
        if (!this.isOnline) {
            return false;
        }

        try {
            this.emit('syncStarted', { type: 'eventData' });

            const response = await fetch(`/api/checkin/${eventSlug}/offline-data/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error('Failed to fetch event data');

            const data = await response.json();

            await this.db.saveEvent(data.event);
            await this.db.saveTickets(data.tickets);
            await this.db.saveSwagItems(data.swagItems || []);

            this.emit('syncCompleted', { type: 'eventData', count: data.tickets.length });
            return true;
        } catch (error) {
            this.emit('syncError', { type: 'eventData', error });
            return false;
        }
    }

    async syncNow() {
        if (this.isSyncing || !this.isOnline) return;

        this.isSyncing = true;
        this.emit('syncStarted', { type: 'full' });

        try {
            const unsyncedCheckins = await this.db.getUnsyncedCheckins();
            const unsyncedSwag = await this.db.getUnsyncedSwagCollections();

            for (const checkin of unsyncedCheckins) {
                await this.syncCheckin(checkin);
            }

            for (const swag of unsyncedSwag) {
                await this.syncSwagCollection(swag);
            }

            this.emit('syncCompleted', {
                type: 'full',
                checkins: unsyncedCheckins.length,
                swag: unsyncedSwag.length
            });

        } catch (error) {
            this.emit('syncError', { type: 'full', error });
        } finally {
            this.isSyncing = false;
        }
    }

    async syncCheckin(checkin) {
        try {
            const response = await fetch('/api/checkin/sync/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    ticketCode: checkin.ticketCode,
                    checkedInAt: checkin.timestamp,
                    notes: checkin.notes
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Sync failed');
            }

            const result = await response.json();
            await this.db.markCheckinSynced(checkin.localId, result.reference);
            this.emit('checkinSynced', checkin);

        } catch (error) {
            this.emit('checkinSyncError', { checkin, error });
        }
    }

    async syncSwagCollection(swagCollection) {
        try {
            const response = await fetch('/api/checkin/swag/sync/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    ticketCode: swagCollection.ticketCode,
                    swagItemId: swagCollection.swagItemId,
                    collectedAt: swagCollection.timestamp
                })
            });

            if (!response.ok) throw new Error('Swag sync failed');

            await this.db.markSwagCollectionSynced(swagCollection.localId);

        } catch (error) {
            // Swag sync failed
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    emit(event, data) {
        const listeners = this.eventListeners.get(event) || [];
        listeners.forEach(callback => callback(data));
    }

    async getOfflineStatus() {
        const unsyncedCheckins = await this.db.getUnsyncedCheckins();
        const unsyncedSwag = await this.db.getUnsyncedSwagCollections();

        return {
            isOnline: this.isOnline,
            isSyncing: this.isSyncing,
            pendingCheckins: unsyncedCheckins.length,
            pendingSwag: unsyncedSwag.length
        };
    }
}

window.OfflineSyncManager = OfflineSyncManager;
window.offlineSync = null;

document.addEventListener('DOMContentLoaded', async () => {
    window.offlineSync = await new OfflineSyncManager().init();
});
