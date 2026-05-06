// src/index.js — Entry point
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const config = require('./core/config');
const logger = require('./core/logger');
const database = require('./core/database');
const apiRouter = require('./routes/api');

const app = express();

// ─── MIDDLEWARE ───────────────────────────────────────────────────
app.use(cors({ origin: '*' }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logger
app.use((req, res, next) => {
  logger.debug('HTTP', `${req.method} ${req.path}`, { ip: req.ip });
  next();
});

// Static frontend
app.use(express.static(path.join(__dirname, '..', 'public')));

// API routes
app.use('/api', apiRouter);

// SPA fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

// Global error handler
app.use((err, req, res, next) => {
  logger.error('Server', 'Unhandled error', { error: err.message });
  res.status(500).json({ error: 'INTERNAL_ERROR', message: err.message });
});

// ─── START ────────────────────────────────────────────────────────
async function start() {
  logger.info('Server', 'Starting Expense Tracker...', { env: config.NODE_ENV });

  // Initialize DB
  database.connect();

  app.listen(config.PORT, () => {
    logger.info('Server', `Running on port ${config.PORT}`, {
      url: `http://localhost:${config.PORT}`,
      env: config.NODE_ENV
    });
  });
}

start().catch(err => {
  logger.critical('Server', 'Failed to start', { error: err.message });
  process.exit(1);
});
