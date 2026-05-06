// src/validators/expenseValidator.js
const { ValidationError } = require('../core/exceptions');

const ALLOWED_CATEGORIES = [
  'food', 'transport', 'housing', 'health', 'entertainment',
  'shopping', 'education', 'travel', 'salary', 'freelance',
  'investment', 'gift', 'other'
];

const ALLOWED_TYPES = ['expense', 'income'];

class ExpenseValidator {
  static validate(data) {
    const errors = [];

    // amount
    const amount = Number(data.amount);
    if (!data.amount && data.amount !== 0) errors.push(['amount', 'Required']);
    else if (isNaN(amount)) errors.push(['amount', 'Must be a number']);
    else if (amount <= 0) errors.push(['amount', 'Must be greater than 0']);
    else if (amount > 999999999) errors.push(['amount', 'Too large']);

    // type
    const type = data.type || 'expense';
    if (!ALLOWED_TYPES.includes(type)) errors.push(['type', `Must be one of: ${ALLOWED_TYPES.join(', ')}`]);

    // category
    const category = data.category || 'other';
    if (!ALLOWED_CATEGORIES.includes(category)) errors.push(['category', `Invalid category`]);

    // description
    if (data.description && String(data.description).length > 200) {
      errors.push(['description', 'Max 200 characters']);
    }

    // date
    if (data.date) {
      const d = new Date(data.date);
      if (isNaN(d.getTime())) errors.push(['date', 'Invalid date format']);
    }

    if (errors.length) {
      const [field, msg] = errors[0];
      throw new ValidationError(field, msg);
    }

    return {
      amount: parseFloat(amount.toFixed(2)),
      type,
      category,
      description: (data.description || '').trim().slice(0, 200),
      date: data.date || new Date().toISOString().slice(0, 10),
      currency: data.currency || 'USD'
    };
  }

  static get allowedCategories() { return ALLOWED_CATEGORIES; }
  static get allowedTypes() { return ALLOWED_TYPES; }
}

module.exports = ExpenseValidator;
