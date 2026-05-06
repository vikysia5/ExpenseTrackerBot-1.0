// src/routes/api.js
const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const config = require('../core/config');
const logger = require('../core/logger');
const userService = require('../services/userService');
const expenseService = require('../services/expenseService');
const { statistics, activityLog } = require('../observers/eventBus');
const { ResponseFactory } = require('../patterns/builders');
const { AppError, UnauthorizedError } = require('../core/exceptions');

// ─── TELEGRAM INIT DATA VALIDATION ───────────────────────────────
function validateTelegramData(initData) {
  if (!initData) return null;

  // In dev mode, accept a simple JSON user object
  if (config.IS_DEV && initData.startsWith('{')) {
    try { return JSON.parse(initData); } catch { return null; }
  }

  try {
    const params = new URLSearchParams(initData);
    const hash = params.get('hash');
    if (!hash) return null;

    params.delete('hash');
    const dataCheckString = [...params.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}=${v}`)
      .join('\n');

    const secretKey = crypto.createHmac('sha256', 'WebAppData')
      .update(config.BOT_TOKEN || 'test').digest();
    const expectedHash = crypto.createHmac('sha256', secretKey)
      .update(dataCheckString).digest('hex');

    if (expectedHash !== hash && !config.IS_DEV) return null;

    const userParam = params.get('user');
    return userParam ? JSON.parse(userParam) : null;
  } catch (e) {
    logger.warning('Auth', 'initData parse failed', { error: e.message });
    return null;
  }
}

// ─── AUTH MIDDLEWARE ──────────────────────────────────────────────
async function authMiddleware(req, res, next) {
  try {
    const initData = req.headers['x-telegram-init-data'] || req.query.initData;

    let telegramUser = validateTelegramData(initData);

    // Dev fallback
    if (!telegramUser && config.IS_DEV) {
      telegramUser = { id: req.headers['x-dev-user-id'] || '12345', first_name: 'Dev', last_name: 'User' };
    }

    if (!telegramUser) throw new UnauthorizedError('Invalid Telegram data');

    const user = await userService.findOrCreate(telegramUser);
    req.user = user;
    req.telegramUser = telegramUser;
    next();
  } catch (err) {
    if (err instanceof AppError) {
      return res.status(err.statusCode).json(err.toDict());
    }
    logger.error('Auth', 'Middleware error', { error: err.message });
    res.status(401).json({ error: 'UNAUTHORIZED', message: 'Authentication failed' });
  }
}

// ─── ERROR HANDLER ────────────────────────────────────────────────
function handleError(err, res) {
  if (err instanceof AppError) {
    logger.warning('API', `AppError: ${err.code}`, { message: err.message });
    return res.status(err.statusCode).json(err.toDict());
  }
  logger.error('API', 'Unhandled error', { error: err.message, stack: err.stack });
  res.status(500).json({ error: 'INTERNAL_ERROR', message: 'Something went wrong' });
}

// ─── ROUTES ──────────────────────────────────────────────────────

// Health check
router.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Get current user
router.get('/me', authMiddleware, async (req, res) => {
  try {
    const stats = statistics.getStats(req.user.id);
    res.json(ResponseFactory.success({ user: req.user, stats }));
  } catch (err) { handleError(err, res); }
});

// Update user settings
router.patch('/me', authMiddleware, async (req, res) => {
  try {
    const { currency } = req.body;
    if (currency) {
      await userService.updateCurrency(req.user.id, currency);
    }
    res.json(ResponseFactory.success({ updated: true }));
  } catch (err) { handleError(err, res); }
});

// Get all expenses
router.get('/expenses', authMiddleware, async (req, res) => {
  try {
    const { sort, period, category } = req.query;
    const result = await expenseService.getAll(req.user.id, { sort, period, category });
    res.json(ResponseFactory.success(result));
  } catch (err) { handleError(err, res); }
});

// Create expense
router.post('/expenses', authMiddleware, async (req, res) => {
  try {
    const result = await expenseService.create(req.user.id, req.body);
    res.status(201).json(ResponseFactory.success(result, 'Expense created'));
  } catch (err) { handleError(err, res); }
});

// Delete expense
router.delete('/expenses/:id', authMiddleware, async (req, res) => {
  try {
    const result = await expenseService.delete(req.user.id, req.params.id);
    res.json(ResponseFactory.success(result, 'Expense deleted'));
  } catch (err) { handleError(err, res); }
});

// Get report
router.get('/report', authMiddleware, async (req, res) => {
  try {
    const { type = 'category' } = req.query;
    const report = await expenseService.getReport(req.user.id, type);
    res.json(ResponseFactory.success(report));
  } catch (err) { handleError(err, res); }
});

// Get categories
router.get('/categories', (req, res) => {
  res.json(ResponseFactory.success(expenseService.getCategories()));
});

// Get activity log
router.get('/activity', authMiddleware, async (req, res) => {
  try {
    const logs = activityLog.getLogs(req.user.id);
    res.json(ResponseFactory.success({ logs }));
  } catch (err) { handleError(err, res); }
});

module.exports = router;
