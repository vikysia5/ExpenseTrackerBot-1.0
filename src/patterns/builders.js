// src/patterns/builders.js
// ПР-8: Factory Method + Builder patterns

// ─── BUILDER: Expense object builder ─────────────────────────────
class ExpenseBuilder {
  constructor(amount) {
    if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) {
      throw new Error('Amount is required and must be positive');
    }
    this._expense = {
      amount: parseFloat(Number(amount).toFixed(2)),
      type: 'expense',
      category: 'other',
      description: '',
      currency: 'USD',
      date: new Date().toISOString().slice(0, 10),
    };
  }

  type(t) { this._expense.type = t; return this; }
  category(c) { this._expense.category = c; return this; }
  description(d) { this._expense.description = String(d).slice(0, 200); return this; }
  currency(c) { this._expense.currency = c; return this; }
  date(d) { this._expense.date = d; return this; }
  forUser(userId) { this._expense.user_id = userId; return this; }

  build() {
    if (!this._expense.user_id) throw new Error('user_id is required');
    return { ...this._expense };
  }
}

// ─── FACTORY: Notification message factory ────────────────────────
class NotificationFactory {
  static _templates = {
    expense_created: (data) => `✅ Added ${data.type}: ${data.currency} ${data.amount} — ${data.category}`,
    expense_deleted: (data) => `🗑 Deleted expense: ${data.currency} ${data.amount}`,
    budget_alert:    (data) => `⚠️ Budget alert: spent ${data.percent}% of monthly budget`,
    welcome:         (data) => `👋 Welcome to Expense Tracker, ${data.name}!`,
    report_ready:    (data) => `📊 Your ${data.period} report is ready`,
  };

  static create(type, data = {}) {
    const tpl = this._templates[type];
    if (!tpl) throw new Error(`Unknown notification type: ${type}`);
    return { type, message: tpl(data), data, createdAt: new Date().toISOString() };
  }

  // OCP: add new notification types without changing factory
  static register(type, templateFn) {
    this._templates[type] = templateFn;
  }
}

// ─── FACTORY: Response factory ────────────────────────────────────
class ResponseFactory {
  static success(data, message = 'OK') {
    return { success: true, message, data };
  }
  static error(code, message, extra = {}) {
    return { success: false, error: code, message, ...extra };
  }
  static paginated(items, total, page = 1, limit = 20) {
    return {
      success: true,
      data: items,
      pagination: { total, page, limit, pages: Math.ceil(total / limit) }
    };
  }
}

module.exports = { ExpenseBuilder, NotificationFactory, ResponseFactory };
