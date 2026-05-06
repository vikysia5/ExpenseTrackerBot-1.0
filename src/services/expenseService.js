// src/services/expenseService.js
// SRP: expense business logic only | All patterns from Module 3

const database = require('../core/database');
const logger = require('../core/logger');
const { ExpenseNotFoundError, DatabaseError, ValidationError } = require('../core/exceptions');
const { bus, statistics } = require('../observers/eventBus');
const { SortStrategyFactory, FilterByPeriod, ReportStrategyFactory } = require('../strategies/sortStrategy');
const { ExpenseBuilder, NotificationFactory } = require('../patterns/builders');
const ExpenseValidator = require('../validators/expenseValidator');
const { timer, gatherSafe, runBackground } = require('../core/decorators');

// CONSTANTS — no magic numbers (ПР-11 refactoring)
const DEFAULT_PAGE_SIZE = 50;
const MAX_EXPORT_ROWS = 1000;

class ExpenseService {
  constructor(db) {
    this.db = db;
    // Apply timer decorator to key methods (ПР-9 Decorator)
    this.getAll = timer(this.getAll.bind(this), 'expenseService.getAll');
    this.create = timer(this.create.bind(this), 'expenseService.create');
  }

  // ─── CREATE ──────────────────────────────────────────────────────
  async create(userId, rawData) {
    logger.info('ExpenseService', 'create start', { userId, category: rawData.category });

    // Validate input (ПР-10)
    const validated = ExpenseValidator.validate(rawData);

    // Use Builder pattern (ПР-8)
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

    logger.info('ExpenseService', 'Expense created', { id: data.id, amount: data.amount });

    // Emit event to all observers (ПР-9 Observer) — non-blocking background
    runBackground(
      () => bus.emit('expense:created', {
        userId, amount: data.amount, category: data.category,
        currency: data.currency, type: data.type
      }),
      'emit expense:created'
    );

    // Build notification (ПР-8 Factory)
    const notification = NotificationFactory.create('expense_created', {
      type: data.type, currency: data.currency,
      amount: data.amount, category: data.category
    });

    return { expense: data, notification };
  }

  // ─── GET ALL (async parallel fetch: ПР-12) ───────────────────────
  async getAll(userId, opts = {}) {
    logger.debug('ExpenseService', 'getAll', { userId, opts });

    const { sort = 'date_desc', period, category } = opts;

    // Parallel fetch: expenses + user stats simultaneously (ПР-12 gather)
    const [expensesResult, statsData] = await gatherSafe(
      this._fetchExpenses(userId),
      Promise.resolve(statistics.getStats(userId))
    );

    let expenses = expensesResult || [];

    // Apply filter strategy (ПР-9 Strategy)
    if (period === 'month') expenses = FilterByPeriod.thisMonth(expenses);
    else if (period === 'week') expenses = FilterByPeriod.thisWeek(expenses);
    if (category) expenses = FilterByPeriod.byCategory(expenses, category);

    // Apply sort strategy (ПР-9 Strategy + ПР-8 Factory)
    const strategy = SortStrategyFactory.create(sort);
    expenses = strategy.sort(expenses);

    const total = expenses.reduce((s, e) => e.type === 'expense' ? s + Number(e.amount) : s, 0);
    const income = expenses.reduce((s, e) => e.type === 'income' ? s + Number(e.amount) : s, 0);

    logger.debug('ExpenseService', 'getAll done', { count: expenses.length });
    return { expenses: expenses.slice(0, DEFAULT_PAGE_SIZE), total, income, stats: statsData };
  }

  async _fetchExpenses(userId) {
    const { data, error } = await this.db.client
      .from('expenses')
      .select('*')
      .eq('user_id', userId)
      .order('date', { ascending: false });

    if (error) throw new DatabaseError('fetch expenses', error.message);
    return data || [];
  }

  // ─── DELETE ──────────────────────────────────────────────────────
  async delete(userId, expenseId) {
    logger.info('ExpenseService', 'delete', { userId, expenseId });

    const { data: existing } = await this.db.client
      .from('expenses').select('*').eq('id', expenseId).eq('user_id', userId).single();

    if (!existing) throw new ExpenseNotFoundError(expenseId);

    const { error } = await this.db.client
      .from('expenses').delete().eq('id', expenseId).eq('user_id', userId);

    if (error) throw new DatabaseError('delete expense', error.message);

    runBackground(
      () => bus.emit('expense:deleted', { userId, amount: existing.amount, category: existing.category }),
      'emit expense:deleted'
    );

    return { deleted: true, expense: existing };
  }

  // ─── REPORT (Strategy pattern ПР-9) ──────────────────────────────
  async getReport(userId, type = 'category') {
    logger.info('ExpenseService', 'getReport', { userId, type });
    const expenses = await this._fetchExpenses(userId);
    const onlyExpenses = expenses.filter(e => e.type === 'expense');
    const strategy = ReportStrategyFactory.create(type);
    return strategy.generate(onlyExpenses);
  }

  // ─── GET CATEGORIES ──────────────────────────────────────────────
  getCategories() {
    return ExpenseValidator.allowedCategories.map(c => ({
      id: c,
      label: c.charAt(0).toUpperCase() + c.slice(1),
      emoji: CATEGORY_EMOJIS[c] || '💰'
    }));
  }
}

const CATEGORY_EMOJIS = {
  food: '🍔', transport: '🚗', housing: '🏠', health: '💊',
  entertainment: '🎮', shopping: '🛍', education: '📚', travel: '✈️',
  salary: '💵', freelance: '💻', investment: '📈', gift: '🎁', other: '📦'
};

module.exports = new ExpenseService(require('../core/database'));
