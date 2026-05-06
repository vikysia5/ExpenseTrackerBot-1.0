// src/strategies/sortStrategy.js
// ПР-9: Strategy Pattern — стратегії сортування та фільтрації витрат

// ─── ABSTRACT STRATEGY ───────────────────────────────────────────
class SortStrategy {
  sort(expenses) { throw new Error('sort() must be implemented'); }
  get name() { return 'base'; }
}

// Strategy 1: Sort by date (newest first)
class SortByDateDesc extends SortStrategy {
  sort(expenses) {
    return [...expenses].sort(
      (a, b) => new Date(b.date || b.created_at) - new Date(a.date || a.created_at)
    );
  }
  get name() { return 'date_desc'; }
}

// Strategy 2: Sort by amount (highest first)
class SortByAmountDesc extends SortStrategy {
  sort(expenses) {
    return [...expenses].sort((a, b) => Number(b.amount) - Number(a.amount));
  }
  get name() { return 'amount_desc'; }
}

// Strategy 3: Sort by category alphabetically
class SortByCategory extends SortStrategy {
  sort(expenses) {
    return [...expenses].sort((a, b) =>
      (a.category || '').localeCompare(b.category || '')
    );
  }
  get name() { return 'category'; }
}

// Strategy 4: Sort by amount ascending (budget-friendly view)
class SortByAmountAsc extends SortStrategy {
  sort(expenses) {
    return [...expenses].sort((a, b) => Number(a.amount) - Number(b.amount));
  }
  get name() { return 'amount_asc'; }
}

// ─── STRATEGY FACTORY (ПР-8: Factory Pattern) ────────────────────
class SortStrategyFactory {
  static _registry = {
    date_desc: SortByDateDesc,
    amount_desc: SortByAmountDesc,
    amount_asc: SortByAmountAsc,
    category: SortByCategory,
  };

  static create(name = 'date_desc') {
    const StrategyClass = this._registry[name];
    if (!StrategyClass) {
      const available = Object.keys(this._registry);
      throw new Error(`Unknown strategy '${name}'. Available: ${available.join(', ')}`);
    }
    return new StrategyClass();
  }

  // OCP: register new strategy without modifying factory
  static register(name, cls) {
    this._registry[name] = cls;
  }

  static available() {
    return Object.keys(this._registry);
  }
}

// ─── FILTER STRATEGY ─────────────────────────────────────────────
class FilterByPeriod {
  static thisMonth(expenses) {
    const now = new Date();
    return expenses.filter(e => {
      const d = new Date(e.date || e.created_at);
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
    });
  }

  static thisWeek(expenses) {
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay());
    startOfWeek.setHours(0, 0, 0, 0);
    return expenses.filter(e => new Date(e.date || e.created_at) >= startOfWeek);
  }

  static byCategory(expenses, category) {
    return expenses.filter(e => e.category === category);
  }

  static byDateRange(expenses, from, to) {
    const f = new Date(from), t = new Date(to);
    return expenses.filter(e => {
      const d = new Date(e.date || e.created_at);
      return d >= f && d <= t;
    });
  }
}

// ─── REPORT STRATEGY (ПР-9) ──────────────────────────────────────
class ReportStrategy {
  generate(expenses) { throw new Error('generate() not implemented'); }
}

class MonthlyReport extends ReportStrategy {
  generate(expenses) {
    const byMonth = {};
    expenses.forEach(e => {
      const key = new Date(e.date || e.created_at).toISOString().slice(0, 7);
      byMonth[key] = (byMonth[key] || 0) + Number(e.amount);
    });
    return { type: 'monthly', data: byMonth };
  }
}

class CategoryReport extends ReportStrategy {
  generate(expenses) {
    const byCat = {};
    expenses.forEach(e => {
      byCat[e.category || 'other'] = (byCat[e.category || 'other'] || 0) + Number(e.amount);
    });
    return { type: 'by_category', data: byCat };
  }
}

class ReportStrategyFactory {
  static _registry = { monthly: MonthlyReport, category: CategoryReport };
  static create(type = 'monthly') {
    const Cls = this._registry[type];
    if (!Cls) throw new Error(`Unknown report type: ${type}`);
    return new Cls();
  }
}

module.exports = {
  SortStrategyFactory, FilterByPeriod,
  ReportStrategyFactory, MonthlyReport, CategoryReport
};
