/**
 * API Service - Singleton Pattern
 * Handles all communication with backend
 */
class ApiService {
  static _instance = null;

  constructor() {
    if (ApiService._instance) return ApiService._instance;
    this.baseURL = window.ENV_API_URL || 'https://your-api.railway.app/api/v1';
    this.token = localStorage.getItem('et_token');
    ApiService._instance = this;
  }

  static getInstance() {
    if (!ApiService._instance) new ApiService();
    return ApiService._instance;
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('et_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('et_token');
    localStorage.removeItem('et_user');
  }

  get headers() {
    const h = { 'Content-Type': 'application/json' };
    if (this.token) h['Authorization'] = `Bearer ${this.token}`;
    return h;
  }

  async request(method, path, body = null) {
    const opts = { method, headers: this.headers };
    if (body) opts.body = JSON.stringify(body);
    try {
      const res = await fetch(`${this.baseURL}${path}`, opts);
      if (res.status === 204) return null;
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Request failed');
      return data;
    } catch (e) {
      Logger.getInstance().error(`API ${method} ${path}`, e.message);
      throw e;
    }
  }

  // AUTH
  async register(email, password, username) {
    return this.request('POST', '/auth/register', { email, password, username });
  }
  async login(email, password) {
    return this.request('POST', '/auth/login', { email, password });
  }
  async telegramAuth(initData) {
    return this.request('POST', '/auth/telegram', { init_data: initData });
  }
  async getMe() {
    return this.request('GET', '/auth/me');
  }

  // TRANSACTIONS
  async getTransactions(params = {}) {
    const q = new URLSearchParams(Object.fromEntries(
      Object.entries(params).filter(([, v]) => v != null)
    )).toString();
    return this.request('GET', `/expenses${q ? '?' + q : ''}`);
  }
  async createTransaction(data) {
    return this.request('POST', '/expenses', data);
  }
  async updateTransaction(id, data) {
    return this.request('PUT', `/expenses/${id}`, data);
  }
  async deleteTransaction(id) {
    return this.request('DELETE', `/expenses/${id}`);
  }
  async getStats(month) {
    return this.request('GET', `/expenses/stats${month ? '?month=' + month : ''}`);
  }

  // CATEGORIES
  async getCategories() {
    return this.request('GET', '/categories');
  }
  async createCategory(data) {
    return this.request('POST', '/categories', data);
  }
  async deleteCategory(id) {
    return this.request('DELETE', `/categories/${id}`);
  }
}

/**
 * Logger - Singleton Pattern
 */
class Logger {
  static _instance = null;

  constructor() {
    if (Logger._instance) return Logger._instance;
    Logger._instance = this;
  }

  static getInstance() {
    if (!Logger._instance) new Logger();
    return Logger._instance;
  }

  _log(level, msg, data) {
    const ts = new Date().toISOString().slice(11, 23);
    const line = data ? `[${ts}] ${level} | ${msg} | ${JSON.stringify(data)}` : `[${ts}] ${level} | ${msg}`;
    if (level === 'ERROR') console.error(line);
    else console.log(line);
  }

  info(msg, data) { this._log('INFO', msg, data); }
  error(msg, data) { this._log('ERROR', msg, data); }
  debug(msg, data) { this._log('DEBUG', msg, data); }
}

/**
 * EventBus - Observer Pattern
 */
class EventBus {
  static _instance = null;
  _listeners = {};

  constructor() {
    if (EventBus._instance) return EventBus._instance;
    EventBus._instance = this;
  }

  static getInstance() {
    if (!EventBus._instance) new EventBus();
    return EventBus._instance;
  }

  on(event, cb) {
    if (!this._listeners[event]) this._listeners[event] = [];
    this._listeners[event].push(cb);
  }

  off(event, cb) {
    if (!this._listeners[event]) return;
    this._listeners[event] = this._listeners[event].filter(fn => fn !== cb);
  }

  emit(event, data) {
    Logger.getInstance().debug(`EventBus.emit: ${event}`);
    (this._listeners[event] || []).forEach(cb => cb(data));
  }
}

/**
 * ExpenseBuilder - Builder Pattern
 */
class ExpenseBuilder {
  constructor() {
    this._data = {
      type: 'expense',
      amount: 0,
      currency: 'USD',
      category_id: null,
      comment: null,
      payment_method: 'card',
      transaction_date: new Date().toISOString(),
      tag_ids: [],
    };
  }

  setType(type) { this._data.type = type; return this; }
  setAmount(amount, currency = 'USD') { this._data.amount = parseFloat(amount); this._data.currency = currency; return this; }
  setCategory(id) { this._data.category_id = id; return this; }
  setComment(c) { this._data.comment = c; return this; }
  setPaymentMethod(m) { this._data.payment_method = m; return this; }
  setDate(d) { this._data.transaction_date = d || new Date().toISOString(); return this; }

  build() {
    if (!this._data.amount || this._data.amount <= 0) throw new Error('Amount must be positive');
    Logger.getInstance().debug('ExpenseBuilder.build', this._data);
    return { ...this._data };
  }
}

/**
 * SortStrategy - Strategy Pattern
 */
const SortStrategies = {
  date: (a, b) => new Date(b.transaction_date) - new Date(a.transaction_date),
  amount: (a, b) => b.amount - a.amount,
  category: (a, b) => ((a.category?.name || '') > (b.category?.name || '') ? 1 : -1),
};

function sortTransactions(items, strategy = 'date') {
  return [...items].sort(SortStrategies[strategy] || SortStrategies.date);
}

// Export globals
window.ApiService = ApiService;
window.Logger = Logger;
window.EventBus = EventBus;
window.ExpenseBuilder = ExpenseBuilder;
window.sortTransactions = sortTransactions;
