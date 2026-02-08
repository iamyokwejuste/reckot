import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";

export default class extends Controller {
  static targets = ["toggle", "syncButton", "statusBadge", "pendingCount", "indicator", "result", "notification"];
  static values = {
    eventSlug: String,
    orgSlug: String,
    syncInterval: { type: Number, default: 300000 }
  };

  connect() {
    this.db = null;
    this.dbName = 'reckot_offline';
    this.dbVersion = 1;
    this.isOnline = navigator.onLine;
    this.isSyncing = false;
    this.isOfflineMode = false;
    this.syncTimer = null;
    this.eventListeners = new Map();

    this.init();
  }

  disconnect() {
    if (this.db) {
      this.db.close();
    }
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
    }
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
  }

  async init() {
    try {
      await this.openDatabase();
      this.setupNetworkListeners();
      this.startPeriodicSync();
      await this.checkOfflineMode();
      this.updateStatusUI();

      // Global reference for backward compatibility
      window.checkinOffline = this;
    } catch (error) {
      console.error('[CheckinOffline] Failed to initialize:', error);
    }
  }

  openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

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
    if (!this.db) await this.openDatabase();
    const transaction = this.db.transaction(storeName, mode);
    return transaction.objectStore(storeName);
  }

  // Settings
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

  // Event data
  async saveEvent(eventData) {
    const store = await this.getStore('events', 'readwrite');
    eventData.syncedAt = Date.now();
    return new Promise((resolve, reject) => {
      const request = store.put(eventData);
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

  // Tickets
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

  // Check-ins
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

  // Swag
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

  // Network handling
  setupNetworkListeners() {
    this.handleOnline = () => {
      this.isOnline = true;
      this.updateStatusUI();
      this.showNotification('Back online - syncing data...', 'success');
      this.syncNow();
    };

    this.handleOffline = () => {
      this.isOnline = false;
      this.updateStatusUI();
      this.showNotification('Offline mode - check-ins will sync later', 'warning');
    };

    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);

    // Periodic connectivity check
    setInterval(async () => {
      const wasOnline = this.isOnline;
      const isOnline = await this.checkConnectivity();
      if (isOnline !== wasOnline) {
        this.isOnline = isOnline;
        if (isOnline) {
          this.handleOnline();
        } else {
          this.handleOffline();
        }
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
    }, this.syncIntervalValue);
  }

  // Offline mode toggle
  async checkOfflineMode() {
    this.isOfflineMode = await this.getSetting('offlineMode') || false;
    if (this.hasToggleTarget) {
      this.toggleTarget.checked = this.isOfflineMode;
    }
  }

  async toggleOfflineMode(event) {
    const enabled = event.target.checked;
    this.isOfflineMode = enabled;
    await this.saveSetting('offlineMode', enabled);

    if (enabled) {
      await this.syncEventData();
      this.showNotification('Offline mode enabled - data cached', 'success');
    } else {
      this.showNotification('Offline mode disabled', 'info');
    }

    this.updateStatusUI();
  }

  async syncEventData() {
    if (!this.isOnline || !this.hasEventSlugValue || !this.hasOrgSlugValue) {
      return false;
    }

    if (this.hasSyncButtonTarget) {
      this.syncButtonTarget.disabled = true;
      const icon = this.syncButtonTarget.querySelector('i[data-lucide]');
      if (icon) {
        icon.setAttribute('data-lucide', 'loader-2');
        icon.classList.add('animate-spin');
        if (typeof lucide !== 'undefined') {
          lucide.createIcons();
        }
      }
    }

    try {
      const response = await fetch(`/api/checkin/${this.orgSlugValue}/${this.eventSlugValue}/offline-data/`, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) throw new Error('Failed to fetch event data');

      const data = await response.json();

      await this.saveEvent(data.event);
      await this.saveTickets(data.tickets);
      await this.saveSwagItems(data.swagItems || []);

      this.showNotification(`Cached ${data.tickets.length} tickets for offline use`, 'success');
      this.updateStatusUI();
      return true;
    } catch (error) {
      console.error('[CheckinOffline] Sync failed:', error);
      this.showNotification('Failed to sync event data', 'error');
      return false;
    } finally {
      if (this.hasSyncButtonTarget) {
        this.syncButtonTarget.disabled = false;
        // Restore the icon
        const icon = this.syncButtonTarget.querySelector('i[data-lucide]');
        if (icon) {
          icon.setAttribute('data-lucide', 'refresh-cw');
          icon.classList.remove('animate-spin');
          // Re-initialize lucide icons
          if (typeof lucide !== 'undefined') {
            lucide.createIcons();
          }
        }
      }
    }
  }

  async syncNow() {
    if (this.isSyncing || !this.isOnline) return;

    this.isSyncing = true;

    try {
      const unsyncedCheckins = await this.getUnsyncedCheckins();
      const unsyncedSwag = await this.getUnsyncedSwagCollections();

      for (const checkin of unsyncedCheckins) {
        await this.syncCheckin(checkin);
      }

      for (const swag of unsyncedSwag) {
        await this.syncSwagCollection(swag);
      }

      if (unsyncedCheckins.length > 0 || unsyncedSwag.length > 0) {
        this.showNotification(
          `Synced ${unsyncedCheckins.length} check-ins and ${unsyncedSwag.length} swag collections`,
          'success'
        );
      }

      this.updateStatusUI();
    } catch (error) {
      console.error('[CheckinOffline] Sync error:', error);
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
      await this.markCheckinSynced(checkin.localId, result.reference);
    } catch (error) {
      console.error('[CheckinOffline] Checkin sync error:', error);
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

      await this.markSwagCollectionSynced(swagCollection.localId);
    } catch (error) {
      console.error('[CheckinOffline] Swag sync error:', error);
    }
  }

  // UI updates
  async updateStatusUI() {
    const status = await this.getOfflineStatus();

    if (this.hasStatusBadgeTarget) {
      const classes = [
        'inline-flex', 'items-center', 'rounded-full', 'border',
        'px-2.5', 'py-0.5', 'text-xs', 'font-semibold'
      ];

      if (status.isOnline) {
        classes.push('border-success/20', 'bg-success/10', 'text-success');
        this.statusBadgeTarget.textContent = 'Online';
      } else {
        classes.push('border-warning/20', 'bg-warning/10', 'text-warning');
        this.statusBadgeTarget.textContent = 'Offline';
      }

      this.statusBadgeTarget.className = classes.join(' ');
    }

    if (this.hasPendingCountTarget) {
      const total = status.pendingCheckins + status.pendingSwag;
      if (total > 0) {
        this.pendingCountTarget.textContent = `${total} pending`;
        this.pendingCountTarget.classList.remove('hidden');
      } else {
        this.pendingCountTarget.classList.add('hidden');
      }
    }

    if (this.hasIndicatorTarget) {
      this.indicatorTarget.classList.toggle('hidden', status.isOnline);
    }
  }

  async getOfflineStatus() {
    const unsyncedCheckins = await this.getUnsyncedCheckins();
    const unsyncedSwag = await this.getUnsyncedSwagCollections();

    return {
      isOnline: this.isOnline,
      isSyncing: this.isSyncing,
      pendingCheckins: unsyncedCheckins.length,
      pendingSwag: unsyncedSwag.length
    };
  }

  showNotification(message, type = 'info') {
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

    const container = document.getElementById('notification-container') || document.body;
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
}
