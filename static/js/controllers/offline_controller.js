import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";

export default class extends Controller {
  static values = {
    dbName: { type: String, default: 'reckot_offline' },
    dbVersion: { type: Number, default: 1 }
  };

  connect() {
    this.db = null;
    this.stores = {
      events: 'events',
      organizations: 'organizations',
      drafts: 'drafts',
      syncQueue: 'sync_queue',
      settings: 'settings'
    };

    this.init();
    this.setupOfflineIndicator();
    this.bindNetworkEvents();
  }

  disconnect() {
    if (this.db) {
      this.db.close();
    }
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
  }

  async init() {
    try {
      this.db = await this.openDatabase();
      window.ReckotOffline = this;
    } catch (error) {
      console.error('[Offline] Failed to initialize:', error);
    }
  }

  openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbNameValue, this.dbVersionValue);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (e) => {
        const db = e.target.result;

        if (!db.objectStoreNames.contains(this.stores.events)) {
          db.createObjectStore(this.stores.events, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(this.stores.organizations)) {
          db.createObjectStore(this.stores.organizations, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(this.stores.drafts)) {
          const drafts = db.createObjectStore(this.stores.drafts, { keyPath: 'id', autoIncrement: true });
          drafts.createIndex('type', 'type', { unique: false });
        }
        if (!db.objectStoreNames.contains(this.stores.syncQueue)) {
          const queue = db.createObjectStore(this.stores.syncQueue, { keyPath: 'id', autoIncrement: true });
          queue.createIndex('timestamp', 'timestamp', { unique: false });
        }
        if (!db.objectStoreNames.contains(this.stores.settings)) {
          db.createObjectStore(this.stores.settings, { keyPath: 'key' });
        }
      };
    });
  }

  async ensureDb() {
    if (!this.db) {
      await this.init();
    }
  }

  async getSetting(key) {
    await this.ensureDb();
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(this.stores.settings, 'readonly');
      const store = tx.objectStore(this.stores.settings);
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result?.value);
      request.onerror = () => reject(request.error);
    });
  }

  async setSetting(key, value) {
    await this.ensureDb();
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(this.stores.settings, 'readwrite');
      const store = tx.objectStore(this.stores.settings);
      const request = store.put({ key, value });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async isOfflineModeEnabled() {
    const setting = await this.getSetting('offlineMode');
    return setting === true;
  }

  async setOfflineMode(enabled) {
    await this.setSetting('offlineMode', enabled);
    if (enabled && 'serviceWorker' in navigator) {
      await this.registerServiceWorker();
    }
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/static/sw.js');
        console.log('[ServiceWorker] Registered:', registration);
      } catch (error) {
        console.error('[ServiceWorker] Registration failed:', error);
      }
    }
    return null;
  }

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
      const tx = this.db.transaction(this.stores.syncQueue, 'readwrite');
      const store = tx.objectStore(this.stores.syncQueue);
      const request = store.add(item);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async getSyncQueue() {
    await this.ensureDb();
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(this.stores.syncQueue, 'readonly');
      const store = tx.objectStore(this.stores.syncQueue);
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async removeFromSyncQueue(id) {
    await this.ensureDb();
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(this.stores.syncQueue, 'readwrite');
      const store = tx.objectStore(this.stores.syncQueue);
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

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
  }

  getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  // Offline Indicator
  setupOfflineIndicator() {
    this.indicator = document.createElement('div');
    this.indicator.id = 'offline-indicator';
    this.indicator.className = 'fixed bottom-4 right-4 z-50 hidden';
    this.indicator.innerHTML = `
      <div class="flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-sm font-medium shadow-lg backdrop-blur-sm">
        <svg class="w-4 h-4 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 010 12.728m-3.536-3.536a4 4 0 010-5.656m-7.072 7.072a4 4 0 010-5.656m-3.536 3.536a9 9 0 010-12.728"/>
        </svg>
        <span>Working Offline</span>
      </div>
    `;
    document.body.appendChild(this.indicator);
    this.updateIndicator();
  }

  bindNetworkEvents() {
    this.handleOnline = () => {
      this.updateIndicator();
      this.trySync();
    };

    this.handleOffline = () => {
      this.updateIndicator();
    };

    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
  }

  updateIndicator() {
    if (navigator.onLine) {
      this.indicator.classList.add('hidden');
    } else {
      this.indicator.classList.remove('hidden');
    }
  }

  async trySync() {
    const result = await this.syncPendingChanges();
    if (result.synced > 0) {
      this.showSyncNotification(result.synced);
    }
  }

  showSyncNotification(count) {
    const notification = document.createElement('div');
    notification.className = 'fixed bottom-4 right-4 z-50 flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm font-medium shadow-lg backdrop-blur-sm';
    notification.innerHTML = `
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
      </svg>
      <span>Synced ${count} change${count > 1 ? 's' : ''}</span>
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }
}
