// src/core/logger.js
// ПР-10: Логування — структуровані JSON-логи з рівнями

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARNING: 2,
  ERROR: 3,
  CRITICAL: 4
};

// ─── SINGLETON PATTERN (ПР-8) ────────────────────────────────────
class Logger {
  static _instance = null;

  constructor() {
    if (Logger._instance) return Logger._instance;
    this._level = LOG_LEVELS[process.env.LOG_LEVEL || 'INFO'];
    this._jsonFormat = process.env.NODE_ENV === 'production';
    Logger._instance = this;
  }

  static getInstance() {
    if (!Logger._instance) new Logger();
    return Logger._instance;
  }

  _format(level, module, message, extra = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      module,
      message,
      ...extra
    };
    return this._jsonFormat
      ? JSON.stringify(entry)
      : `${entry.timestamp} [${level.padEnd(8)}] ${module}: ${message}${
          Object.keys(extra).length ? ' ' + JSON.stringify(extra) : ''
        }`;
  }

  _log(level, levelKey, module, message, extra) {
    if (LOG_LEVELS[levelKey] >= this._level) {
      const out = this._format(levelKey, module, message, extra);
      if (levelKey === 'ERROR' || levelKey === 'CRITICAL') {
        console.error(out);
      } else {
        console.log(out);
      }
    }
  }

  debug(module, message, extra = {}) { this._log(0, 'DEBUG', module, message, extra); }
  info(module, message, extra = {}) { this._log(1, 'INFO', module, message, extra); }
  warning(module, message, extra = {}) { this._log(2, 'WARNING', module, message, extra); }
  error(module, message, extra = {}) { this._log(3, 'ERROR', module, message, extra); }
  critical(module, message, extra = {}) { this._log(4, 'CRITICAL', module, message, extra); }
}

module.exports = Logger.getInstance();
