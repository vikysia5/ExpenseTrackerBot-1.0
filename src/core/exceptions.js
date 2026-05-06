// src/core/exceptions.js
// ПР-10: Ієрархія власних виключень

class AppError extends Error {
  constructor(message, code = 'APP_ERROR', statusCode = 500) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.statusCode = statusCode;
    this.message = message;
  }
  toDict() { return { error: this.code, message: this.message }; }
}

// Validation errors
class ValidationError extends AppError {
  constructor(field, message) {
    super(`Field '${field}': ${message}`, 'VALIDATION_ERROR', 422);
    this.field = field;
  }
  toDict() { return { error: this.code, message: this.message, field: this.field }; }
}

// Business logic errors
class BusinessError extends AppError {
  constructor(message, code = 'BUSINESS_ERROR') {
    super(message, code, 400);
  }
}

class ExpenseNotFoundError extends BusinessError {
  constructor(id) {
    super(`Expense #${id} not found`, 'EXPENSE_NOT_FOUND');
    this.statusCode = 404;
  }
}

class UserNotFoundError extends BusinessError {
  constructor(id) {
    super(`User #${id} not found`, 'USER_NOT_FOUND');
    this.statusCode = 404;
  }
}

class UnauthorizedError extends AppError {
  constructor(msg = 'Unauthorized') {
    super(msg, 'UNAUTHORIZED', 401);
  }
}

class CategoryNotFoundError extends BusinessError {
  constructor(id) {
    super(`Category #${id} not found`, 'CATEGORY_NOT_FOUND');
    this.statusCode = 404;
  }
}

// Infrastructure errors
class DatabaseError extends AppError {
  constructor(operation, detail) {
    super(`DB: operation '${operation}' failed: ${detail}`, 'DB_ERROR', 503);
  }
}

module.exports = {
  AppError, ValidationError, BusinessError,
  ExpenseNotFoundError, UserNotFoundError,
  UnauthorizedError, CategoryNotFoundError, DatabaseError
};
