// src/core/database.js
// Singleton for Supabase connection — falls back to in-memory mock
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

    if (config.SUPABASE_URL && config.SUPABASE_ANON_KEY) {
      try {
        const { createClient } = require('@supabase/supabase-js');
        this._client = createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY);
        logger.info('Database', 'Connected to Supabase');
        return this._client;
      } catch (e) {
        logger.warning('Database', 'Supabase client failed, using mock: ' + e.message);
      }
    } else {
      logger.warning('Database', 'No Supabase credentials — using in-memory mock');
    }

    this._client = this._createMockClient();
    return this._client;
  }

  _createMockClient() {
    // Simple in-memory store — works for demo / testing without Supabase
    const store = {
      users: [],
      expenses: [],
      user_settings: []
    };

    let _autoId = 1;
    const nextId = () => _autoId++;

    const chain = (data, error = null) => ({
      data, error,
      then(cb) { return Promise.resolve(cb({ data, error })); },
      single() { return Promise.resolve({ data: Array.isArray(data) ? data[0] || null : data, error }); },
      order() { return chain(data, error); },
      limit(n) { return chain(Array.isArray(data) ? data.slice(0, n) : data, error); },
    });

    const mockTable = (tableName) => {
      const tbl = () => store[tableName] || (store[tableName] = []);

      return {
        select(cols) {
          return {
            eq(col, val) {
              const filtered = tbl().filter(r => String(r[col]) === String(val));
              return {
                ...chain(filtered),
                single: () => Promise.resolve({ data: filtered[0] || null, error: null }),
                order: (c, opts) => {
                  const sorted = [...filtered].sort((a,b) => {
                    if (opts && opts.ascending === false) return String(b[c]).localeCompare(String(a[c]));
                    return String(a[c]).localeCompare(String(b[c]));
                  });
                  return chain(sorted);
                },
                eq(col2, val2) {
                  const f2 = filtered.filter(r => String(r[col2]) === String(val2));
                  return { ...chain(f2), single: () => Promise.resolve({ data: f2[0] || null, error: null }) };
                }
              };
            },
            order(col, opts) {
              const all = [...tbl()].sort((a,b) => {
                if (opts && opts.ascending === false) return String(b[col]).localeCompare(String(a[col]));
                return String(a[col]).localeCompare(String(b[col]));
              });
              return {
                ...chain(all),
                eq(c, v) {
                  const filtered = all.filter(r => String(r[c]) === String(v));
                  return { ...chain(filtered) };
                }
              };
            },
            ...chain(tbl()),
            single: () => Promise.resolve({ data: tbl()[0] || null, error: null })
          };
        },

        insert(rows) {
          const arr = Array.isArray(rows) ? rows : [rows];
          const inserted = arr.map(r => {
            const record = { ...r, id: nextId(), created_at: new Date().toISOString() };
            store[tableName].push(record);
            return record;
          });
          return {
            select() {
              return {
                single: () => Promise.resolve({ data: inserted[0], error: null }),
                ...chain(inserted)
              };
            },
            ...chain(inserted)
          };
        },

        update(data) {
          return {
            eq(col, val) {
              const idx = tbl().findIndex(r => String(r[col]) === String(val));
              if (idx >= 0) Object.assign(store[tableName][idx], data);
              return {
                select() {
                  return {
                    single: () => Promise.resolve({ data: store[tableName][idx] || null, error: null })
                  };
                },
                ...chain(store[tableName][idx] || null)
              };
            }
          };
        },

        delete() {
          return {
            eq(col, val) {
              store[tableName] = tbl().filter(r => String(r[col]) !== String(val));
              return { ...chain(null), then: (cb) => Promise.resolve(cb({ data: null, error: null })) };
            }
          };
        }
      };
    };

    logger.info('Database', 'Mock DB ready');
    return { from: mockTable };
  }

  get client() {
    return this._client || this.connect();
  }
}

module.exports = Database.getInstance();
