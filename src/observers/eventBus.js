// src/observers/eventBus.js
// ПР-9: Observer Pattern — EventBus для подій системи

const logger = require('../core/logger');

class EventBus {
  static _instance = null;
  _listeners = new Map();

  constructor() {
    if (EventBus._instance) return EventBus._instance;
    EventBus._instance = this;
  }

  static getInstance() {
    if (!EventBus._instance) new EventBus();
    return EventBus._instance;
  }

  // Subscribe to an event
  on(event, handler) {
    if (!this._listeners.has(event)) this._listeners.set(event, []);
    this._listeners.get(event).push(handler);
    logger.debug('EventBus', `Handler subscribed`, { event });
    return () => this.off(event, handler); // returns unsubscribe fn
  }

  // Unsubscribe
  off(event, handler) {
    const handlers = this._listeners.get(event) || [];
    this._listeners.set(event, handlers.filter(h => h !== handler));
  }

  // Emit event — notify all subscribers
  async emit(event, data = {}) {
    const handlers = this._listeners.get(event) || [];
    logger.debug('EventBus', `Emitting event`, { event, handlersCount: handlers.length });

    const results = await Promise.allSettled(
      handlers.map(h => Promise.resolve(h(data)))
    );

    results.forEach((r, i) => {
      if (r.status === 'rejected') {
        logger.error('EventBus', `Handler ${i} failed for event ${event}`, {
          error: r.reason?.message
        });
      }
    });

    return results;
  }
}

// ─── CONCRETE OBSERVERS ──────────────────────────────────────────

// Observer 1: Activity Logger
class ActivityLogObserver {
  constructor() {
    this.logs = [];
  }

  handle(data) {
    const entry = { ...data, loggedAt: new Date().toISOString() };
    this.logs.push(entry);
    logger.info('ActivityLog', `[EVENT] ${data.event}`, {
      userId: data.userId,
      amount: data.amount
    });
  }

  getLogs(userId) {
    return this.logs.filter(l => l.userId === userId);
  }
}

// Observer 2: Budget Alert Observer
class BudgetAlertObserver {
  constructor(budgetLimitUSD = 1000) {
    this.budgetLimit = budgetLimitUSD;
    this.alerts = [];
  }

  async handle(data) {
    if (data.event === 'expense:created' && data.amount > this.budgetLimit * 0.5) {
      const alert = {
        userId: data.userId,
        message: `⚠️ Large expense: ${data.amount} ${data.currency || 'USD'}`,
        at: new Date().toISOString()
      };
      this.alerts.push(alert);
      logger.warning('BudgetAlert', alert.message, { userId: data.userId });
    }
  }

  getAlerts(userId) {
    return this.alerts.filter(a => a.userId === userId);
  }
}

// Observer 3: Statistics Observer
class StatisticsObserver {
  constructor() {
    this.stats = new Map(); // userId -> { total, count, byCategory }
  }

  handle(data) {
    const userId = String(data.userId);
    if (!this.stats.has(userId)) {
      this.stats.set(userId, { total: 0, count: 0, byCategory: {} });
    }

    const s = this.stats.get(userId);

    if (data.event === 'expense:created') {
      s.total += Number(data.amount) || 0;
      s.count += 1;
      const cat = data.category || 'other';
      s.byCategory[cat] = (s.byCategory[cat] || 0) + Number(data.amount);
      logger.debug('Statistics', `Updated stats for user ${userId}`, s);
    } else if (data.event === 'expense:deleted') {
      s.total = Math.max(0, s.total - (Number(data.amount) || 0));
      s.count = Math.max(0, s.count - 1);
    }
  }

  getStats(userId) {
    return this.stats.get(String(userId)) || { total: 0, count: 0, byCategory: {} };
  }
}

// Export singleton bus and observer instances
const bus = EventBus.getInstance();
const activityLog = new ActivityLogObserver();
const budgetAlert = new BudgetAlertObserver();
const statistics = new StatisticsObserver();

// Wire observers to bus
bus.on('expense:created', (d) => activityLog.handle({ ...d, event: 'expense:created' }));
bus.on('expense:created', (d) => budgetAlert.handle({ ...d, event: 'expense:created' }));
bus.on('expense:created', (d) => statistics.handle({ ...d, event: 'expense:created' }));
bus.on('expense:deleted', (d) => activityLog.handle({ ...d, event: 'expense:deleted' }));
bus.on('expense:deleted', (d) => statistics.handle({ ...d, event: 'expense:deleted' }));
bus.on('user:registered', (d) => activityLog.handle({ ...d, event: 'user:registered' }));

module.exports = { bus, activityLog, budgetAlert, statistics };
