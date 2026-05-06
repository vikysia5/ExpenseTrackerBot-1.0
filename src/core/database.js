// src/core/database.js
// Singleton для з'єднання з Supabase (безкоштовна PostgreSQL)
const { createClient } = require('@supabase/supabase-js');
const config = require('./config');
const logger = require('./logger');

class Database {
  static _instance = null;
  _client = null;

  constructor() {
    if (Database._instance) return Database._instance;
    Database._instance = this;
  }

  static getInstance() {
    if (!Database._instance) new Database();
    return Database._instance;
  }

  connect() {
    if (this._client) return this._client;

    if (!config.SUPABASE_URL || !config.SUPABASE_ANON_KEY) {
      logger.warning('Database', 'Supabase not configured — using mock mode');
      this._client = this._createMockClient();
      return this._client;
    }

    this._client = createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY);
    logger.info('Database', 'Connected to Supabase', { url: config.SUPABASE_URL });
    return this._client;
  }

  // Mock client for development without Supabase
  _createMockClient() {
    const store = { users: [], expenses: [], categories: [] };

    const mockTable = (tableName) => ({
      select: (cols = '*') => ({
        eq: (col, val) => ({
          single: async () => {
            const item = store[tableName]?.find(r => r[col] === val);
            return { data: item || null, error: null };
          },
          order: () => ({ data: store[tableName]?.filter(r => r[col] === val) || [], error: null }),
          then: (cb) => cb({ data: store[tableName]?.filter(r => r[col] === val) || [], error: null })
        }),
        order: (col, opts) => ({
          eq: (c, v) => ({ data: store[tableName]?.filter(r => r[c] === v) || [], error: null }),
          data: store[tableName] || [],
          error: null
        }),
        data: store[tableName] || [],
        error: null
      }),
      insert: (rows) => ({
        select: () => ({
          single: async () => {
            const arr = Array.isArray(rows) ? rows : [rows];
            arr.forEach(r => {
              r.id = r.id || Date.now() + Math.random();
              r.created_at = r.created_at || new Date().toISOString();
              store[tableName] = store[tableName] || [];
              store[tableName].push(r);
            });
            return { data: arr[0], error: null };
          }
        })
      }),
      update: (data) => ({
        eq: (col, val) => ({
          select: () => ({
            single: async () => {
              const idx = store[tableName]?.findIndex(r => r[col] === val);
              if (idx >= 0) Object.assign(store[tableName][idx], data);
              return { data: store[tableName]?.[idx] || null, error: null };
            }
          })
        })
      }),
      delete: () => ({
        eq: (col, val) => ({
          data: null,
          error: null,
          then: (cb) => {
            store[tableName] = store[tableName]?.filter(r => r[col] !== val) || [];
            cb({ data: null, error: null });
          }
        })
      })
    });

    return { from: mockTable };
  }

  get client() {
    return this._client || this.connect();
  }
}

module.exports = Database.getInstance();
