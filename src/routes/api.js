// src/routes/api.js — REST API (PR-5: OpenAPI-style endpoints)
const express = require('express');
const router  = express.Router();
const crypto  = require('crypto');
const config  = require('../core/config');
const logger  = require('../core/logger');
const userService    = require('../services/userService');
const expenseService = require('../services/expenseService');
const { statistics, activityLog } = require('../observers/eventBus');
const { ResponseFactory } = require('../patterns/builders');
const { AppError, UnauthorizedError } = require('../core/exceptions');

// ─── TELEGRAM INIT DATA VALIDATION ──────────────────────────────
function parseTelegramInitData(initData) {
  if (!initData) return null;

  // Plain JSON — dev mode or browser testing
  if (initData.startsWith('{')) {
    try { return JSON.parse(initData); } catch { return null; }
  }

  // Real Telegram initData — validate hash
  try {
    const params = new URLSearchParams(initData);
    const hash = params.get('hash');
    if (!hash) return null;

    const userParam = params.get('user');
    if (!userParam) return null;

    // Skip hash check in dev mode (no real BOT_TOKEN)
    if (!config.IS_DEV && config.BOT_TOKEN) {
      params.delete('hash');
      const checkStr = [...params.entries()]
        .sort(([a],[b]) => a.localeCompare(b))
        .map(([k,v]) => `${k}=${v}`)
        .join('\n');

      const secret = crypto.createHmac('sha256', 'WebAppData')
        .update(config.BOT_TOKEN).digest();
      const expected = crypto.createHmac('sha256', secret)
        .update(checkStr).digest('hex');

      if (expected !== hash) {
        logger.warning('Auth', 'Hash mismatch');
        return null;
      }
    }

    return JSON.parse(userParam);
  } catch (e) {
    logger.warning('Auth', 'initData parse error: ' + e.message);
    return null;
  }
}

// ─── AUTH MIDDLEWARE ─────────────────────────────────────────────
async function auth(req, res, next) {
  try {
    // Accept from header or query param
    const raw = req.headers['x-telegram-init-data']
      || req.headers['x-init-data']
      || req.query.initData
      || '';

    let telegramUser = parseTelegramInitData(raw);

    // Dev fallback: allow x-dev-user-id header or default mock user
    if (!telegramUser) {
      const devId = req.headers['x-dev-user-id'] || '12345';
      if (config.IS_DEV) {
        telegramUser = { id: devId, first_name: 'Dev', last_name: 'User', username: 'devuser' };
        logger.debug('Auth', 'Dev fallback user', { id: devId });
      } else {
        throw new UnauthorizedError('Missing or invalid Telegram auth');
      }
    }

    req.user = await userService.findOrCreate(telegramUser);
    req.telegramUser = telegramUser;
    logger.debug('Auth', 'Authenticated', { userId: req.user.id });
    next();
  } catch (err) {
    const status = err instanceof AppError ? err.statusCode : 401;
    const body   = err instanceof AppError ? err.toDict() : { error: 'UNAUTHORIZED', message: 'Auth failed' };
    res.status(status).json(body);
  }
}

// ─── ERROR WRAPPER ────────────────────────────────────────────────
function wrap(handler) {
  return async (req, res, next) => {
    try {
      await handler(req, res, next);
    } catch (err) {
      if (err instanceof AppError) {
        logger.warning('API', err.code, { message: err.message });
        return res.status(err.statusCode).json(err.toDict());
      }
      logger.error('API', 'Unhandled: ' + err.message);
      res.status(500).json({ error: 'INTERNAL_ERROR', message: err.message });
    }
  };
}

// ─── ROUTES ──────────────────────────────────────────────────────

// Health check — no auth needed
router.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString(), env: config.NODE_ENV });
});

// GET /me
router.get('/me', auth, wrap(async (req, res) => {
  const stats = statistics.getStats(req.user.id);
  res.json(ResponseFactory.success({ user: req.user, stats }));
}));

// PATCH /me
router.patch('/me', auth, wrap(async (req, res) => {
  const { currency } = req.body;
  if (currency) await userService.updateCurrency(req.user.id, currency);
  res.json(ResponseFactory.success({ updated: true }));
}));

// GET /expenses
router.get('/expenses', auth, wrap(async (req, res) => {
  const { sort, period, category } = req.query;
  const result = await expenseService.getAll(req.user.id, { sort, period, category });
  res.json(ResponseFactory.success(result));
}));

// POST /expenses
router.post('/expenses', auth, wrap(async (req, res) => {
  const result = await expenseService.create(req.user.id, req.body);
  res.status(201).json(ResponseFactory.success(result, 'Expense created'));
}));

// DELETE /expenses/:id
router.delete('/expenses/:id', auth, wrap(async (req, res) => {
  const result = await expenseService.delete(req.user.id, req.params.id);
  res.json(ResponseFactory.success(result, 'Deleted'));
}));

// GET /report
router.get('/report', auth, wrap(async (req, res) => {
  const report = await expenseService.getReport(req.user.id, req.query.type || 'category');
  res.json(ResponseFactory.success(report));
}));

// GET /categories — no auth needed
router.get('/categories', (req, res) => {
  res.json(ResponseFactory.success(expenseService.getCategories()));
});

// GET /activity
router.get('/activity', auth, wrap(async (req, res) => {
  const logs = activityLog.getLogs(req.user.id);
  res.json(ResponseFactory.success({ logs }));
}));

module.exports = router;
