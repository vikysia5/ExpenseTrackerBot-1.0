// src/core/config.js
// PR-8: Singleton Pattern
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
    this.PORT             = parseInt(process.env.PORT) || 3000;
    this.NODE_ENV         = process.env.NODE_ENV || 'development';
    this.BOT_TOKEN        = process.env.BOT_TOKEN || '';
    this.SUPABASE_URL     = process.env.SUPABASE_URL || '';
    this.SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || '';
    this.APP_URL          = process.env.APP_URL || ('http://localhost:' + this.PORT);
    // IS_DEV: allow browser testing when no BOT_TOKEN
    this.IS_DEV           = this.NODE_ENV !== 'production' || !this.BOT_TOKEN;
    this._loaded = true;
    return this;
  }

  validate() {
    if (!this.BOT_TOKEN)         console.warn('[Config] BOT_TOKEN not set');
    if (!this.SUPABASE_URL)      console.warn('[Config] SUPABASE_URL not set — mock DB');
    if (!this.SUPABASE_ANON_KEY) console.warn('[Config] SUPABASE_ANON_KEY not set — mock DB');
    return this;
  }
}

const config = AppConfig.getInstance();
config.load();
config.validate();
module.exports = config;
