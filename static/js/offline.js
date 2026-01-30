const ReckotOffline = {
    DB_NAME: 'reckot_offline',
    DB_VERSION: 1,
    STORES: {
        events: 'events',
        organizations: 'organizations',
        drafts: 'drafts',
        syncQueue: 'sync_queue',
        settings: 'settings'
    },
    db: null,

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (e) => {
                const db = e.target.result;

                if (!db.objectStoreNames.contains(this.STORES.events)) {
                    db.createObjectStore(this.STORES.events, { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains(this.STORES.organizations)) {
                    db.createObjectStore(this.STORES.organizations, { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains(this.STORES.drafts)) {
                    const drafts = db.createObjectStore(this.STORES.drafts, { keyPath: 'id', autoIncrement: true });
                    drafts.createIndex('type', 'type', { unique: false });
                }
                if (!db.objectStoreNames.contains(this.STORES.syncQueue)) {
                    const queue = db.createObjectStore(this.STORES.syncQueue, { keyPath: 'id', autoIncrement: true });
                    queue.createIndex('timestamp', 'timestamp', { unique: false });
                }
                if (!db.objectStoreNames.contains(this.STORES.settings)) {
                    db.createObjectStore(this.STORES.settings, { keyPath: 'key' });
                }
            };
        });
    },

    async getSetting(key) {
        await this.ensureDb();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(this.STORES.settings, 'readonly');
            const store = tx.objectStore(this.STORES.settings);
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result?.value);
            request.onerror = () => reject(request.error);
        });
    },

    async setSetting(key, value) {
        await this.ensureDb();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(this.STORES.settings, 'readwrite');
            const store = tx.objectStore(this.STORES.settings);
            const request = store.put({ key, value });
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    },

    async isOfflineModeEnabled() {
        const setting = await this.getSetting('offlineMode');
        return setting === true;
    },

    async setOfflineMode(enabled) {
        await this.setSetting('offlineMode', enabled);
        if (enabled && 'serviceWorker' in navigator) {
            await this.registerServiceWorker();
        }
    },

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                return registration;
            } catch (error) {

            }
        }
    },

    async ensureDb() {
        if (!this.db) {
            await this.init();
        }
    },

    async saveDraft(type, data) {
        await this.ensureDb();
        const draft = {
            type,
            data,
            timestamp: Date.now(),
            synced: false
        };
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(this.STORES.drafts, 'readwrite');
            const store = tx.objectStore(this.STORES.drafts);
            const request = store.put(draft);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    },

    async getDraft(type) {
        await this.ensureDb();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(this.STORES.drafts, 'readonly');
            const store = tx.objectStore(this.STORES.drafts);
            const index = store.index('type');
            const request = index.getAll(type);
            request.onsuccess = () => {
                const drafts = request.result;
                resolve(drafts.length > 0 ? drafts[drafts.length - 1] : null);
            };
            request.onerror = () => reject(request.error);
        });
    },

    async deleteDraft(id) {
        await this.ensureDb();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(this.STORES.drafts, 'readwrite');
            const store = tx.objectStore(this.STORES.drafts);
            const request = store.delete(id);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    },

    async addToSyncQueue(action, endpoint, data) {
        await this.ensureDb();
        const item = {
            action,
            endpoint,
            data,
            timestamp: Date.now(),
            retries: 0
        };
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(this.STORES.syncQueue, 'readwrite');
            const store = tx.objectStore(this.STORES.syncQueue);
            const request = store.add(item);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    },

    async getSyncQueue() {
        await this.ensureDb();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(this.STORES.syncQueue, 'readonly');
            const store = tx.objectStore(this.STORES.syncQueue);
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    },

    async removeFromSyncQueue(id) {
        await this.ensureDb();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(this.STORES.syncQueue, 'readwrite');
            const store = tx.objectStore(this.STORES.syncQueue);
            const request = store.delete(id);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    },

    async syncPendingChanges() {
        if (!navigator.onLine) {
            return { synced: 0, failed: 0 };
        }

        const queue = await this.getSyncQueue();
        let synced = 0;
        let failed = 0;

        for (const item of queue) {
            try {
                const response = await fetch(item.endpoint, {
                    method: item.action,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify(item.data)
                });

                if (response.ok) {
                    await this.removeFromSyncQueue(item.id);
                    synced++;
                } else {
                    failed++;
                }
            } catch (error) {
                failed++;
            }
        }

        return { synced, failed };
    },

    getCSRFToken() {
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    },

    async cacheData(storeName, data) {
        await this.ensureDb();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);

            if (Array.isArray(data)) {
                data.forEach(item => store.put(item));
            } else {
                store.put(data);
            }

            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
        });
    },

    async getCachedData(storeName, id = null) {
        await this.ensureDb();
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, 'readonly');
            const store = tx.objectStore(storeName);
            const request = id ? store.get(id) : store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
};

const FormPersistence = {
    PREFIX: 'reckot_form_',

    save(formId, data) {
        const key = this.PREFIX + formId;
        localStorage.setItem(key, JSON.stringify({
            data,
            timestamp: Date.now()
        }));
    },

    load(formId) {
        const key = this.PREFIX + formId;
        const stored = localStorage.getItem(key);
        if (!stored) return null;

        try {
            const parsed = JSON.parse(stored);
            const hourAgo = Date.now() - (60 * 60 * 1000);
            if (parsed.timestamp < hourAgo) {
                this.clear(formId);
                return null;
            }
            return parsed.data;
        } catch {
            return null;
        }
    },

    clear(formId) {
        const key = this.PREFIX + formId;
        localStorage.removeItem(key);
    },

    autoSave(formId, form, interval = 2000) {
        let timeout;

        const save = () => {
            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => {
                if (key !== 'csrfmiddlewaretoken') {
                    data[key] = value;
                }
            });
            this.save(formId, data);
        };

        const debouncedSave = () => {
            clearTimeout(timeout);
            timeout = setTimeout(save, interval);
        };

        form.addEventListener('input', debouncedSave);
        form.addEventListener('change', debouncedSave);

        return {
            stop: () => {
                form.removeEventListener('input', debouncedSave);
                form.removeEventListener('change', debouncedSave);
                clearTimeout(timeout);
            },
            saveNow: save
        };
    },

    restore(formId, form) {
        const data = this.load(formId);
        if (!data) return false;

        Object.entries(data).forEach(([key, value]) => {
            const field = form.elements[key];
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = value === 'on' || value === true;
                } else if (field.type === 'file') {

                } else {
                    field.value = value;
                }
                field.dispatchEvent(new Event('input', { bubbles: true }));
                field.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        return true;
    }
};

const OfflineIndicator = {
    element: null,

    init() {
        this.create();
        this.bindEvents();
        this.update();
    },

    create() {
        this.element = document.createElement('div');
        this.element.id = 'offline-indicator';
        this.element.className = 'fixed bottom-4 right-4 z-50 hidden';
        this.element.innerHTML = `
            <div class="flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-sm font-medium shadow-lg backdrop-blur-sm">
                <svg class="w-4 h-4 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 010 12.728m-3.536-3.536a4 4 0 010-5.656m-7.072 7.072a4 4 0 010-5.656m-3.536 3.536a9 9 0 010-12.728"/>
                </svg>
                <span>Working Offline</span>
            </div>
        `;
        document.body.appendChild(this.element);
    },

    bindEvents() {
        window.addEventListener('online', () => this.update());
        window.addEventListener('offline', () => this.update());
    },

    update() {
        if (navigator.onLine) {
            this.element.classList.add('hidden');
            this.trySync();
        } else {
            this.element.classList.remove('hidden');
        }
    },

    async trySync() {
        const result = await ReckotOffline.syncPendingChanges();
        if (result.synced > 0) {
            this.showSyncNotification(result.synced);
        }
    },

    showSyncNotification(count) {
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 z-50 flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm font-medium shadow-lg backdrop-blur-sm animate-in';
        notification.innerHTML = `
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <span>Synced ${count} change${count > 1 ? 's' : ''}</span>
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
};

document.addEventListener('DOMContentLoaded', async () => {
    await ReckotOffline.init();

    const offlineModeEnabled = await ReckotOffline.isOfflineModeEnabled();
    if (offlineModeEnabled) {
        OfflineIndicator.init();
    }
});

window.ReckotOffline = ReckotOffline;
window.FormPersistence = FormPersistence;
window.OfflineIndicator = OfflineIndicator;
