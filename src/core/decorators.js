// src/core/decorators.js
// ПР-9: Decorator pattern + ПР-12: async utilities

const logger = require('./logger');

// Decorator 1: timer — вимірює час виконання
function timer(fn, label) {
  return async function (...args) {
    const start = Date.now();
    try {
      const result = await fn.apply(this, args);
      logger.debug('Timer', `${label || fn.name} took ${Date.now() - start}ms`);
      return result;
    } catch (e) {
      logger.debug('Timer', `${label || fn.name} failed after ${Date.now() - start}ms`);
      throw e;
    }
  };
}

// Decorator 2: cache — простий in-memory кеш з TTL
function cache(fn, ttlMs = 30000) {
  const store = new Map();
  return async function (...args) {
    const key = JSON.stringify(args);
    const cached = store.get(key);
    if (cached && Date.now() - cached.at < ttlMs) {
      logger.debug('Cache', `HIT: ${fn.name}`, { key });
      return cached.value;
    }
    const result = await fn.apply(this, args);
    store.set(key, { value: result, at: Date.now() });
    logger.debug('Cache', `MISS: ${fn.name}`, { key });
    return result;
  };
}

// Decorator 3: retry — повторює при помилці з backoff
function retry(fn, maxAttempts = 3, delayMs = 500) {
  return async function (...args) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await fn.apply(this, args);
      } catch (err) {
        if (attempt === maxAttempts) throw err;
        const delay = delayMs * Math.pow(2, attempt - 1);
        logger.warning('Retry', `Attempt ${attempt} failed, retrying in ${delay}ms`, {
          fn: fn.name, error: err.message
        });
        await new Promise(r => setTimeout(r, delay));
      }
    }
  };
}

// ─── ASYNC UTILITY: gather with error handling (ПР-12) ───────────
async function gatherSafe(...promises) {
  const results = await Promise.allSettled(promises);
  return results.map(r => r.status === 'fulfilled' ? r.value : null);
}

// Background task runner (ПР-12)
function runBackground(fn, label = 'bg-task') {
  Promise.resolve()
    .then(() => fn())
    .then(() => logger.debug('Background', `${label} completed`))
    .catch(err => logger.error('Background', `${label} failed`, { error: err.message }));
}

module.exports = { timer, cache, retry, gatherSafe, runBackground };
