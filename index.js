// src/index.js — Entry point
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

// Safe requires — don't crash if a module has issues
let config, logger, database, apiRouter;
try {
  config   = require('./core/config');
  logger   = require('./core/logger');
  database = require('./core/database');
  apiRouter = require('./routes/api');
} catch (e) {
  console.error('[FATAL] Module load failed:', e.message);
  process.exit(1);
}

const app = express();
const PORT = process.env.PORT || 3000;

// Resolve public dir — works regardless of cwd
const PUBLIC_DIR = path.resolve(__dirname, '..', 'public');
const INDEX_HTML = path.join(PUBLIC_DIR, 'index.html');

console.log('[Server] public dir:', PUBLIC_DIR);
console.log('[Server] index.html exists:', fs.existsSync(INDEX_HTML));

// ─── MIDDLEWARE ───────────────────────────────────────────────────
app.use(cors({ origin: '*' }));
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true }));

// Request logger
app.use((req, res, next) => {
  logger.debug('HTTP', `${req.method} ${req.path}`);
  next();
});

// ─── STATIC FILES — serve BEFORE api routes ───────────────────────
app.use(express.static(PUBLIC_DIR, {
  index: 'index.html',
  maxAge: '1h'
}));

// ─── API ROUTES ───────────────────────────────────────────────────
app.use('/api', apiRouter);

// ─── SPA FALLBACK — ALL other routes serve index.html ─────────────
app.get('*', (req, res) => {
  if (!fs.existsSync(INDEX_HTML)) {
    return res.status(404).send('index.html not found. Check public/ folder.');
  }
  res.sendFile(INDEX_HTML);
});

// ─── GLOBAL ERROR HANDLER ─────────────────────────────────────────
app.use((err, req, res, _next) => {
  logger.error('Server', 'Unhandled error', { error: err.message });
  res.status(500).json({ error: 'INTERNAL_ERROR', message: err.message });
});

// ─── START ────────────────────────────────────────────────────────
async function start() {
  logger.info('Server', 'Starting Expense Tracker...', { env: process.env.NODE_ENV, port: PORT });

  // Initialize DB (non-fatal — falls back to mock)
  try { database.connect(); }
  catch (e) { logger.warning('Server', 'DB connect failed, using mock', { error: e.message }); }

  app.listen(PORT, '0.0.0.0', () => {
    logger.info('Server', `✅ Running on port ${PORT}`);
    logger.info('Server', `🌐 Open: http://localhost:${PORT}`);
  });
}

start().catch(err => {
  console.error('[FATAL] Failed to start:', err.message);
  process.exit(1);
});
