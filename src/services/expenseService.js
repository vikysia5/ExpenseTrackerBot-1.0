// src/services/expenseService.js
// SRP: expense logic | All Module 3 patterns applied

const database  = require('../core/database');
const logger    = require('../core/logger');
const { ExpenseNotFoundError, DatabaseError } = require('../core/exceptions');
const { bus, statistics } = require('../observers/eventBus');
const { SortStrategyFactory, FilterByPeriod, ReportStrategyFactory } = require('../strategies/sortStrategy');
const { ExpenseBuilder, NotificationFactory } = require('../patterns/builders');
const ExpenseValidator = require('../validators/expenseValidator');
const { timer, gatherSafe, runBackground } = require('../core/decorators');

// CONSTANTS — no magic numbers (PR-11)
const DEFAULT_PAGE_SIZE = 50;

const CATEGORY_EMOJIS = {
  food:'🍔', transport:'🚗', housing:'🏠', health:'💊',
  entertainment:'🎮', shopping:'🛍', education:'📚', travel:'✈️',
  salary:'💵', freelance:'💻', investment:'📈', gift:'🎁', other:'📦'
};

class ExpenseService {
  constructor(db) {
    this.db = db;
    // Apply Decorator pattern (PR-9)
    this.getAll  = timer(this.getAll.bind(this),  'expenseService.getAll');
    this.create  = timer(this.create.bind(this),  'expenseService.create');
  }

  // ─── CREATE ────────────────────────────────────────────────────
  async create(userId, rawData) {
    logger.info('ExpenseService', 'create', { userId, category: rawData.category });

    // Validate (PR-10)
    const validated = ExpenseValidator.validate(rawData);

    // Builder pattern (PR-8)
    const expense = new ExpenseBuilder(validated.amount)
      .type(validated.type)
      .category(validated.category)
      .description(validated.description)
      .currency(validated.currency)
      .date(validated.date)
      .forUser(userId)
      .build();

    const { data, error } = await this.db.client
      .from('expenses')
      .insert(expense)
      .select()
      .single();

    if (error) {
      logger.error('ExpenseService', 'DB insert failed', { error: error.message });
      throw new DatabaseError('insert expense', error.message);
    }

    logger.info('ExpenseService', 'Created', { id: data.id, amount: data.amount });

    // Observer: emit event in background (PR-9 + PR-12)
    runBackground(
      () => bus.emit('expense:created', {
        userId, amount: data.amount, category: data.category,
        currency: data.currency, type: data.type
      }),
      'emit expense:created'
    );

    // Factory: build notification message (PR-8)
    const notification = NotificationFactory.create('expense_created', {
      type: data.type, currency: data.currency,
      amount: data.amount, category: data.category
    });

    return { expense: data, notification };
  }

  // ─── GET ALL — parallel fetch with gather (PR-12) ──────────────
  async getAll(userId, opts = {}) {
    logger.debug('ExpenseService', 'getAll', { userId, opts });
    const { sort = 'date_desc', period, category } = opts;

    // Parallel: expenses + stats (PR-12 Promise.allSettled)
    const [expensesResult] = await gatherSafe(
      this._fetchExpenses(userId),
    );

    let expenses = expensesResult || [];

    // Filter Strategy (PR-9)
    if (period === 'month') expenses = FilterByPeriod.thisMonth(expenses);
    else if (period === 'week') expenses = FilterByPeriod.thisWeek(expenses);
    if (category) expenses = FilterByPeriod.byCategory(expenses, category);

    // Sort Strategy + Factory (PR-9 + PR-8)
    const strategy = SortStrategyFactory.create(sort);
    expenses = strategy.sort(expenses);

    const total  = expenses.filter(e => e.type === 'expense').reduce((s,e) => s + Number(e.amount), 0);
    const income = expenses.filter(e => e.type === 'income').reduce((s,e) => s + Number(e.amount), 0);

    return {
      expenses: expenses.slice(0, DEFAULT_PAGE_SIZE),
      total: parseFloat(total.toFixed(2)),
      income: parseFloat(income.toFixed(2))
    };
  }

  async _fetchExpenses(userId) {
    const result = await this.db.client
      .from('expenses')
      .select('*')
      .order('date', { ascending: false })
      .eq('user_id', userId);

    // Handle both chained and direct result formats
    const data  = result.data  || [];
    const error = result.error || null;

    if (error) throw new DatabaseError('fetch expenses', error.message);
    return Array.isArray(data) ? data : [];
  }

  // ─── DELETE ────────────────────────────────────────────────────
  async delete(userId, expenseId) {
    logger.info('ExpenseService', 'delete', { userId, expenseId });

    // Find first to verify ownership
    const findRes = await this.db.client
      .from('expenses')
      .select('*')
      .eq('id', expenseId)
      .eq('user_id', userId)
      .single();

    const existing = findRes.data;
    if (!existing) throw new ExpenseNotFoundError(expenseId);

    await this.db.client
      .from('expenses')
      .delete()
      .eq('id', expenseId)
      .eq('user_id', userId);

    runBackground(
      () => bus.emit('expense:deleted', { userId, amount: existing.amount }),
      'emit expense:deleted'
    );

    return { deleted: true, expense: existing };
  }

  // ─── REPORT — Strategy pattern (PR-9) ──────────────────────────
  async getReport(userId, type = 'category') {
    const expenses = await this._fetchExpenses(userId);
    const onlyExpenses = expenses.filter(e => e.type === 'expense');
    const strategy = ReportStrategyFactory.create(type);
    return strategy.generate(onlyExpenses);
  }

  getCategories() {
    return ExpenseValidator.allowedCategories.map(c => ({
      id: c,
      label: c.charAt(0).toUpperCase() + c.slice(1),
      emoji: CATEGORY_EMOJIS[c] || '📦'
    }));
  }
}

module.exports = new ExpenseService(database);
