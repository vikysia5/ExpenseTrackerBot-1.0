// src/core/config.js
// ПР-8: Singleton Pattern — єдиний об'єкт конфігурації
require('dotenv').config();

class AppConfig {
  static _instance = null;
  _loaded = false;

  constructor() {
    if (AppConfig._instance) return AppConfig._instance;
    AppConfig._instance = this;
  }

  static getInstance() {
    if (!AppConfig._instance) new AppConfig();
    return AppConfig._instance;
  }

  load() {
    if (this._loaded) return this;

    this.PORT = parseInt(process.env.PORT) || 3000;
    this.NODE_ENV = process.env.NODE_ENV || 'development';
    this.BOT_TOKEN = process.env.BOT_TOKEN || '';
    this.SUPABASE_URL = process.env.SUPABASE_URL || '';
    this.SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || '';
    this.APP_URL = process.env.APP_URL || `http://localhost:${this.PORT}`;
    this.IS_DEV = this.NODE_ENV === 'development';

    this._loaded = true;
    return this;
  }

  validate() {
    const required = ['BOT_TOKEN', 'SUPABASE_URL', 'SUPABASE_ANON_KEY'];
    const missing = required.filter(k => !this[k]);
    if (missing.length) {
      throw new Error(`Missing env vars: ${missing.join(', ')}`);
    }
    return this;
  }
}

const config = AppConfig.getInstance();
config.load();
module.exports = config;
